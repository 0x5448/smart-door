# function to handle API call from WP2 (webpage used by visitor to enter otp and gain access)

import json
import boto3
import time
from boto3.dynamodb.conditions import Key

ACC_D = 'Access denied. Your OTP is wrong or invalid'
ACC_E = 'Access denied. Expired OTP, try again in sometime'
ACC_G = 'Access granted, Welcome!'

TEST_SIZE = 10

dynamo_resource = boto3.resource('dynamodb')
dynamo_passcodes_table = dynamo_resource.Table('passcodes')

def expiry(timestamp):
    return int(time.time()) > int(timestamp)


def match(OTP, input_otp):
    return OTP == input_otp


def query_otp(phone_number):
    response = dynamo_passcodes_table.query(
        KeyConditionExpression=Key('PhoneNumber').eq(phone_number)
    )
    return response['Items'][0]


def lambda_handler(event, context):
    input_phone = event['phone']
    input_otp = event['password']

    try:
        record = query_otp(input_phone)
    except Exception as e:
        record = None
        print(e)

    print(record)

    if record is None:
        message = ACC_D

    expired = expiry(record['ExpTime'])
    matching = match(record['OTP'], input_otp)

    if not expired:
        if matching:
            message = ACC_G
        else:
            message = ACC_D
            print(f'OTP: {record["OTP"]}, i_otp: {input_otp}')
    else:
        message = ACC_E

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }
