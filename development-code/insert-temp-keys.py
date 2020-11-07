import boto3
import json
import random
import time

TEST_SIZE = 10
EXPIRY_5 = 60 * 5

# for testing only
EXPIRY_60 = 60 * 60
test_phone_numbers = ['9487881124', '3159433008', '5852250407', '8532164799', '3429339955', '8904899367', '1015425175', '1242486178', '8053519794', '5184914986']

dynamodb = boto3.client('dynamodb')

def otp():
    return str(random.randint(100001, 999999))

def phone_numbers():
    return [str(random.randint(1000000000, 9999999999)) for _ in range(TEST_SIZE)]

def expiry(range=EXPIRY_5):
    return str(int(time.time()) + range)

def create_item(phone):
    item = dict()
    item['PhoneNumber'] = {'S': phone}
    item['OTP'] = {'S': otp()}
    item['ExpTime'] = {'S': expiry()}
    
    return item


passCount = 0
failCount = 0

for phone_number in test_phone_numbers:
    item = create_item(phone_number)
    try:
        dynamodb.put_item(TableName='passcodes', Item=item)
        passCount += 1
    except Exception as e:
        print(f'Failed {phone_number} due to {e}')
        failCount += 1

print(f'Success: {passCount}, Failed: {failCount}')

print("Pass Count: ", passCount)
print("Fail Count: ", failCount)