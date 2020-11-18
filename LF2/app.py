# function to handle API call from WP2 (webpage used by visitor to enter otp and gain access)

import json
import boto3
import time
from boto3.dynamodb.conditions import Key


dynamo_resource = boto3.resource('dynamodb')
passcodes_table = dynamo_resource.Table('passcodes')
visitors_table = dynamo_resource.Table('visitors')


def void_otp(phone_number):
    password = {
        'PhoneNumber': phone_number,
        'OTP': '-1', # Flag as used
        'ExpTime': int(int(time.time()))  # Expires at current time
    }
    passcodes_table.put_item(Item=password)


def otp_has_expired(timestamp):
    return int(time.time()) > int(timestamp)


def visitor_otp_matches_database_otp(OTP, input_otp):
    return OTP == input_otp


def get_otp_item_by_phone(phone_number):
    response = passcodes_table.query(
        KeyConditionExpression=Key('PhoneNumber').eq(phone_number)
    )
    return response['Items'][0]


def validate_otp(db_item, input_otp):
    if db_item is None:
        return "DENIED"
    if not visitor_otp_matches_database_otp(db_item['OTP'], input_otp):
        return "DENIED"
    elif otp_has_expired(db_item['ExpTime']):
        return "EXPIRED"
    else:
        return "GRANTED"


def get_name_from_externalid(externalid):
    visitor = visitors_table.get_item(Key={'ExternalImageId': externalid})
    name = visitor['Item']['name']
    return name


def lambda_handler(event, context):
    input_phone = event['phone']
    input_otp = event['password']
    input_external_id = event['externalID']

    name = get_name_from_externalid(input_external_id)

    try:
        db_item = get_otp_item_by_phone(input_phone)
    except Exception as e:
        db_item = None
        print(e)
    print("db_item is:", str(db_item))

    status = validate_otp(db_item, input_otp)

    if status == 'GRANTED':
        void_otp(input_phone)

    print(status)

    result = {
        'status': status,
        'name': name
    }

    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


