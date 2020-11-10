from __future__ import print_function
import base64
import boto3
from botocore.exceptions import ClientError
import sys
import cv2
import json
from random import randint
import uuid
import datetime

COLLECTION = 'faces'  # Rekognition collection
REGION = 'us-east-1'
BUCKET = 'smart-door-image-store'  # s3://<ExternalImageId>/<ImageId>
EXPIRY_5 = 60 * 5
 
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
s3_resource = boto3.resource('s3')
kvs_video_client = boto3.client('kinesisvideo')
rekognition = boto3.client("rekognition", REGION)
dynamo_resource = boto3.resource('dynamodb')
dynamo_visitors_table = dynamo_resource.Table("visitors")
dynamo_passcodes_table = dynamo_resource.Table('passcodes')
bucket = "smart-door-image-store"


def index_faces(key, ExternalImageId, attributes=()):
    response = rekognition.index_faces(
        Image={
            "S3Object": {
                "Bucket": BUCKET,
                "Name": key,
            }
        },
        CollectionId=COLLECTION,
        ExternalImageId=ExternalImageId,
        DetectionAttributes=attributes,
    )
    # return response['FaceRecords']['ImageId']
    return


def get_payload_from_event(event):
    # for record in event['Records'] # I think we can just use event['Records'][0]
    # Kinesis data is base64 encoded so decode here
    byte_str = base64.b64decode(event['Records'][0]["kinesis"]["data"])  # of type bytes
    dict_payload = json.loads(byte_str.decode("UTF-8"))
    return dict_payload


# Get an endpoint so that we can send the GET_MEDIA request to it later
def get_get_media_endpoint():
    return kvs_video_client.get_data_endpoint(
        StreamName="Assignment2-KVS1",
        APIName="GET_MEDIA"
    )


# Now that we have the endpoint for GET_MEDIA, we can start a session
# and pass the endpoint_url
def start_kvs_session(endpoint_response):
    return boto3.client(
        'kinesis-video-media',
        endpoint_url=endpoint_response["DataEndpoint"]
    )


# Now that we started a session, we can finally call GET_MEDIA
def get_media_by_fragment_number(fragment_number, kvs_video_media_client):
    return kvs_video_media_client.get_media(
        StreamName="Assignment2-KVS1",
        StartSelector={
            # 'StartSelectorType': 'FRAGMENT_NUMBER',
            'StartSelectorType': 'NOW',
            # 'AfterFragmentNumber': payload['InputInformation']['KinesisVideo']['FragmentNumber']
            # 'AfterFragmentNumber': fragment_number
        }
    )


# Get GET_MEDIA API endpoint, start a sesh, and get the media via the endpoint
def get_media_stream(payload):
    endpoint_response = get_get_media_endpoint()
    kvs_video_media_client = start_kvs_session(endpoint_response)
    fragment_number = payload['InputInformation']['KinesisVideo']['FragmentNumber']
    kvs_stream = get_media_by_fragment_number(fragment_number, kvs_video_media_client)
    return kvs_stream


def get_image_from_stream(payload):
    kvs_stream = get_media_stream(payload)
    clip = kvs_stream['Payload'].read()  # Get the video clip of the payload
    img_temp_location = '/tmp/img_frame.jpg'
    vid_temp_location = '/tmp/stream.avi'

    # print('got here')
    # exit(1)
    with open(vid_temp_location, 'wb') as f:
        # First need to write the clip to a file so we
        # can later extract a frame from it
        f.write(clip)
        vidcap = cv2.VideoCapture(vid_temp_location)  # Capture an img from it
        success, image = vidcap.read()
        cv2.imwrite(img_temp_location, image)  # Save image to file
        return img_temp_location


# Store face in s3 bucket and return ExternalImageId
def upload_visitor_image_to_s3(visitor_image_local_path, ExternalImageId):
    unique_img_id = str(uuid.uuid4())  # Generate a unique identifier for this image
    # Upload the file to S3
    object_key = ExternalImageId + '/' + unique_img_id + '.jpg'
    try:
        response = s3_client.upload_file(visitor_image_local_path, bucket, object_key)
        return object_key
    except ClientError as e:
        logging.error(e)
    return object_key

# Udpate visitor information with new image 
def update_visitor(visitor, s3_object_key):
    external_image_id = visitor['Item']['ExternalImageId']
    name = visitor['Item']['name']
    phone_number = visitor['Item']['phoneNumber']
    
    new_photo = {
        'objectKey' : s3_object_key,
        'bucket' : bucket,
        'createdTimestamp' : datetime.datetime.now().isoformat(timespec='seconds')
    }
    photos = visitor['Item']['photos'].append(new_photo)

    visitor = {
        'ExternalImageId' : external_image_id,
        'name' : name,
        'phoneNumber' : phone_number,
        'photos' : photos
    }
    visitors.put_item(Item=visitor)

#store otp and expiration for known visitor
def store_otp(otp, phone_number, range=EXPIRY_5):
    password = {
        'PhoneNumber': phone_number,
        'OTP': otp,
        'ExpTime': str(int(time.time()) + range)
    }
    passcodes.put_item(Item=password)

# send SMS with OTP if it's a known visitor
def send_sms(otp, phone_number):
    message = "Welcome back! Here is your one time password: \"" + otp + "\". This password will expire in 5 minutes."
    sns_client.publish(PhoneNumber=phone_number, Message=message)


# send SMS requesting access if it's an unknown visitor
def send_review(face_id):
    # TODO: update with group member's phone
    phone_number = 000
    # include face and file ID
    visitor_verification_link = "https://smart-door-b1.s3.amazonaws.com/wp1.html" + "?" + "faceid=" + face_id + "&filename=" + filename

    # TODO: make sure format of variable in URL matches LF0
    message = "Hello, you have recieved a visitor verification request. For more information please go here: " + visitor_verification_link
    sns_client.publish(PhoneNumber=phone_number, Message=message)


def is_known_visitor(dict_payload):
    return len(dict_payload['FaceSearchResponse']) > 0


def get_ExternalImageId(dict_payload):
    return dict_payload['FaceSearchResponse'][0]['MatchedFaces'][0]['Face']['ExternalImageId']


def lambda_handler(event, context):
    payload = get_payload_from_event(event)  # Decode the event record

    ''' If known visitor, do the following:
        1. Store to s3 in visitor's folder:  s3://<ExternalImageId>/<newImg>
        2. Index in Rekognition
        3. Append s3 photo object key to visitors table photos array
        4. Send OTP to visitor
    '''
    if is_known_visitor(payload):
        ExternalImageId = get_ExternalImageId(payload)
        visitor_image_local_path = get_image_from_stream(payload)

        s3_object_key = upload_visitor_image_to_s3(visitor_image_local_path, ExternalImageId)

        # Index new image of known visitor to train model
        index_faces(s3_object_key, ExternalImageId)

        # Return visitor information by finding photoID key in visitor table
        visitor = dynamo_visitors_table.get_item(Key=ExternalImageId)

        # append faceId in visitor dynamoDB object list
        update_visitor(visitor, s3_object_key)

        # add password and expiriation to password dynamo
        phone_number = visitor['Item']['phoneNumber']
        
        # create and store OTP in passwords table
        otp = str(random.randint(100001, 999999))
        store_otp(otp, phone_number)

        # Send sms to returning visitor
        send_sms(otp, phone_number)

    # Else, send visitor info to owner for review
    else:
        # Generate a unique ID for the new visitor
        ExternalImageId = str(uuid.uuid4())

        # store new face in visitors table
        send_review(ExternalImageId)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }