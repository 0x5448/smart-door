import boto3

client = boto3.client('rekognition')
STREAM_PROCESSOR_NAME = 'KVS1-To-KDS1-Stream-Processor'

response = client.create_stream_processor(
    Input={
        'KinesisVideoStream': {
            'Arn': 'arn:aws:kinesisvideo:us-east-1:401806354087:stream/Assignment2-KVS1/1604547889535'
        }
    },
    Output={
        'KinesisDataStream': {
            'Arn': 'arn:aws:kinesis:us-east-1:401806354087:stream/Assignment2-KDS1'
        }
    },
    Name=STREAM_PROCESSOR_NAME,
    Settings={
        'FaceSearch': {
            'CollectionId': 'faces',
            'FaceMatchThreshold': 85
        }
    },
    RoleArn='arn:aws:iam::401806354087:role/stream-processor-role'
)
print(response)
