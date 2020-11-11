# function to handle API call from WP1 (webpage used by owner to add new valid visitor to receive otp and gain access)

import json
import boto3
import random 
import datetime
import time

BUCKET = 'smart-door-image-store'
REGION = 'us-east-1'
COLLECTION = 'faces'
EXPIRY_5 = 60 * 5

# change to relevant s3 web url during deployment
WP1_URL = 'https://smart-door-b1.s3.amazonaws.com/wp1.html' 

sms_client = boto3.client('sns')
s3_client = boto3.client('s3')
rekognition = boto3.client('rekognition', REGION)
dynamodb = boto3.resource('dynamodb')
visitors = dynamodb.Table('visitors')
passcodes = dynamodb.Table('passcodes')

def create_visitor(face_id:str, name:str, phone_number:str, image_name:str) -> dict:
    record = {
        'faceId' : face_id,
        'name' : name,
        'phoneNumber' : phone_number,
        'photos' : [
            {
                'objectKey' : f'{image_name}.jpg',
                'bucket' : 'smart-door-image-store',
                'createdTimestamp' : datetime.datetime.now().isoformat(timespec='seconds')
            }
        ]
    }
    return record
    
def otp():
    return str(random.randint(100001, 999999))

def expiry(range=EXPIRY_5):
    return str(int(time.time()) + range)
    
def create_sms(name, otp, link=WP1_URL):
    message =  f'Hey {name}, Use OTP: {otp} at {link} to gain access. OTP will expire in 5 minutes'
    return message

def send_sms(phone_number, message):
    sms_client.publish(
        PhoneNumber=f'+1{phone_number}',
        Message=message
    )
    
def create_passcode(phone_number:str) -> dict:
    record = {
        'PhoneNumber': phone_number,
        'OTP': otp(),
        'ExpTime': expiry()
    }
    return record
    

def delete_face_from_rekognition(FaceId):
    return rekognition.delete_faces()
        CollectionId=COLLECTION,
        FaceIds=[FaceId]
    )


def delete_visitor_image_from_s3(s3_object_key):
    return s3_client.delete_object(
        Bucket=BUCKET,
        Key=s3_object_key
    )


def lambda_handler(event, context):
    if event['status'] == "accept":
        name = event['name']
        phone_number = event['phone']
        face_id = event['faceID']
        image_name = event['filename']
        
        FaceId = event['FaceId'] # Rekognition FaceId (in case we need to delete it)
        s3_object_key = event['s3_object_key'] # In case we need to delete it from s3
    
        visitor = create_visitor(face_id, name, phone_number, image_name)
        passcode = create_passcode(phone_number)
        message = create_sms(name, passcode['OTP'])
    
        try:
            visitors.put_item(Item=visitor)
            passcodes.put_item(Item=passcode)
            send_sms(phone_number, message)
            message = 'Approved visitor'        
        except Exception as e:
            message = str(e)
            print(e)
    
    # Else, if user is denied, delete all images and classifier info about them
    else:
        face_id = event['faceID']
        delete_face_from_rekognition(FaceId)
        delete_visitor_image_from_s3(s3_object_key)
    
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

