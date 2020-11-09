from __future__ import print_function
import base64
import boto3
from botocore.exceptions import ClientError
import sys
import cv2
import json
from random import randint
import uuid

s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
s3_resource = boto3.resource('s3')
kvs_video_client = boto3.client('kinesisvideo')
dynamo_resource = boto3.resource('dynamodb')
dynamo_visitors_table = dynamo_resource.Table("visitors")
dynamo_passcodes_table = dynamo_resource.Table('passcodes')


def get_payload_from_event(event):
    #for record in event['Records'] # I think we can just use event['Records'][0]
    #Kinesis data is base64 encoded so decode here
    byte_str = base64.b64decode(event['Records'][0]["kinesis"]["data"]) # of type bytes
    dict_payload = json.loads(byte_str.decode("UTF-8"))
    return dict_payload


# Store face in s3 bucket and return faceID
def store_s3(dict_payload, ExternalImageId):
    # First, get an endpoint so that we can send the GET_MEDIA request to it later
    endpoint_response = kvs_video_client.get_data_endpoint(
        StreamName="Assignment2-KVS1",
        APIName="GET_MEDIA"
    )
    
    # Now that we have the endpoint for GET_MEDIA, we can start a session
    # and pass the endpoint_url
    kvs_video_media_client = boto3.client(
        'kinesis-video-media',
        endpoint_url=endpoint_response["DataEndpoint"]
    )
    
    # Now that we started a session, we can finally call GET_MEDIA
    kvs_stream = kvs_video_media_client.get_media(
       StreamName="Assignment2-KVS1",
       StartSelector= {
           'StartSelectorType': 'FRAGMENT_NUMBER',
           #'StartSelectorType': 'NOW',
           'AfterFragmentNumber': dict_payload['InputInformation']['KinesisVideo']['FragmentNumber']
       }
    )

    clip = kvs_stream['Payload'].read() # Get the video clip of the payload
    
    vid_temp_location = '/tmp/stream.avi'
    with open(vid_temp_location, 'wb') as f:
        # First need to write the clip to a file so we 
        # can later extract a frame from it
        f.write(clip)
        
        vidcap = cv2.VideoCapture(vid_temp_location) # Capture an img from it
        success, image = vidcap.read()
        cv2.imwrite('/tmp/tmp_screenshot.jpg', image) # Save image to file
        
        # Upload the file to S3
        bucket = "smart-door-image-store"
        object_name = ExternalImageId + '.jpg'
        try:
            response = s3_client.upload_file('/tmp/tmp_screenshot.jpg' , bucket, object_name) 
            return
        except ClientError as e:
            logging.error(e)
    return


#send SMS with OTP if it's a known visitor
def send_otp(otp, phone_number):
    message = "Welcome back! Here is your one time password: \"" + otp + "\". This password will expire in 5 minutes."  
    sns_client.publish(PhoneNumber=phone_number, Message=message)


#send SMS requesting access if it's an unknown visitor
def send_review(face_id):
    #TODO: update with group member's phone
    phone_number = 000 
    #include face and file ID
    visitor_verification_link = "https://smart-door-b1.s3.amazonaws.com/wp1.html" + "?" + "faceid=" + face_id + "&filename=" + filename
    
    #TODO: make sure format of variable in URL matches LF0
    message = "Hello, you have recieved a visitor verification request. For more information please go here: " + visitor_verification_link
    sns_client.publish(PhoneNumber=phone_number, Message=message)


def is_known_visitor(dict_payload):
    return len(dict_payload['FaceSearchResponse']) > 0
    
    
def get_ExternalImageId(dict_payload):
    return dict_payload['FaceSearchResponse'][0]['MatchedFaces'][0]['Face']['ExternalImageId']


def lambda_handler(event, context):
    #triggered by Kinesis Data Stream
    #data = event['Records']
    dict_payload = get_payload_from_event(event) # Decode the event record
    #matched = data['FaceSearchResponse'][0]['MatchedFaces']

    #if face is a match, store and send otp
    #if matched is not None:
    if is_known_visitor(dict_payload):
        ExternalImageId = get_ExternalImageId(dict_payload)
        
        # TODO Index image to Rekognition to train classifier here
        
        store_s3(dict_payload, ExternalImageId)
        #faceID = store_s3(dict_payload)

        # Return visitor information by finding photoID key in visitor table
        #visitor = dynamo_visitors_table.get_item(Key=faceID)
        #phone_number = visitor['phoneNumber']

        #generate 6 digit OTP
        range_start = 10**(6-1)
        range_end = (10**6)-1
        otp = randint(range_start, range_end)

        #append faceID in visitor dynamoDB object list 

        #add password and expiriation to password dynamo

        #send sms to returning visitor
        #send_otp(otp, phone_number)

    #else send review 
    else:
        ExternalImageId = str(uuid.uuid4()) # This can be the unique ID for the new visitor
        
        #store new face in visitors table
        #send_review(faceID)


    return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }
