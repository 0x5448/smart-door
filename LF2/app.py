# function to handle API call from WP2 (webpage used by visitor to enter otp and gain access)

import json
import boto3
import time
from boto3.dynamodb.conditions import Key

DENIED = 'Access denied. Invalid OTP or time expired. (Must enter OTP within 5 minutes of receiving it.)'
EXPIRED = 'Access denied. Expired OTP, try again in sometime'
GRANTED = 'Access granted. Welcome!'

TEST_SIZE = 10

dynamo_resource = boto3.resource('dynamodb')
dynamo_passcodes_table = dynamo_resource.Table('passcodes')


def otp_has_expired(timestamp):
    return int(time.time()) > int(timestamp)


def visitor_otp_matches_database_otp(OTP, input_otp):
    return OTP == input_otp


def get_otp_item_by_phone(phone_number):
    response = dynamo_passcodes_table.query(
        KeyConditionExpression=Key('PhoneNumber').eq(phone_number)
    )
    return response['Items'][0]


def validate_otp(db_item, input_otp):
    if db_item is None:
        return DENIED
    if not visitor_otp_matches_database_otp(db_item['OTP'], input_otp):
        return DENIED
    elif otp_has_expired(db_item['ExpTime']):
        return EXPIRED
    else:
        return GRANTED


def lambda_handler(event, context):
    input_phone = event['phone']
    input_otp = event['password']

    try:
        db_item = get_otp_item_by_phone(input_phone)
    except Exception as e:
        db_item = None
        print(e)
    print("db_item is:", str(db_item))

    message = validate_otp(db_item, input_otp)
    print(message)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }

