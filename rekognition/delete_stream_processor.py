import boto3

client = boto3.client('rekognition')
STREAM_PROCESSOR_NAME = 'KVS1-To-KDS1-Stream-Processor'

response = client.delete_stream_processor(
    Name=STREAM_PROCESSOR_NAME
)
print(response)
