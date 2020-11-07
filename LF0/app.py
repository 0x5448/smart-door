<<<<<<< HEAD
# hi
import boto3
import json
from random import randint


sns_client = boto3.client('sns')

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

dynamo_resource = boto3.resource('dynamodb')
dynamo_visitors_table = dynamo_resource.Table("visitors")
dynamo_passcodes_table = dynamo_resource.Table('passcodes')


#store face in s3 bucket and return faceID
def store_s3():
    pass


#send SMS with OTP if it's a known visitor
def send_otp(otp, phone_number):
    message = "Welcome back! Here is your one time password: \"" + otp + "\". This password will expire in 5 minutes."  
    sns_client.publish(PhoneNumber=phone_number, Message=message)

#send SMS requesting access if it's an unknown visitor
def send_review(face_id):
    #TODO: update with group member's phone
    phone_number = 000 
    visitor_verification_link = "https://smart-door-b1.s3.amazonaws.com/wp1.html" + "?" + face_id
    
    #TODO: make sure format of variable in URL matches LF0
    message = "Hello, you have recieved a visitor verification request. For more information please go here: " + visitor_verification_link
    sns_client.publish(PhoneNumber=phone_number, Message=message)

    

def lambda_handler(event, context):
    #triggered by Kinesis Data Stream
    #TODO: Parse KDS event "Records", and retrieve the matched face from stream. Starting barebones idea:
    data = event['Records']
    matched = data['FaceSearchResponse'][0]['MatchedFaces'] 

    #if face is a match, store and send otp
    if matched is not None:
        faceID = store_s3(matched)

        #returning visitor information by finding photoID key in visitor table
        visitor = dynamo_visitors_table.get_item(Key=faceID)
        phone_number = visitor['phoneNumber']

        #generate 6 digit OTP
        range_start = 10**(6-1)
        range_end = (10**6)-1
        otp = randint(range_start, range_end)

        #append faceID in visitor dynamoDB object list 

        #add password and expiriation to password dynamo

        #send sms to returning visitor
        send_otp(otp, phone_number)

    #else send review 
    else:
        #store new face in visitors table
        send_review(faceID)


    return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }
=======
# function to handle API call from WP1 (webpage used by owner to add new valid visitor to receive otp and gain access)

import json
import boto3
import random
import datetime
import time

EXPIRY_5 = 60 * 5

# change to relevant s3 web url during deployment
WP1_URL = 'https://smart-door-b1.s3.amazonaws.com/wp1.html'

sms_client = boto3.client('sns')

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


def lambda_handler(event, context):
    name = event['name']
    phone_number = event['phone']
    face_id = event['faceID']
    image_name = event['filename']

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

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
>>>>>>> 4ee060c4636b0827979e30ade690dc81b6b0e193
