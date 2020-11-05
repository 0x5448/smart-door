import boto3

STREAM_PROCESSOR_NAME = 'KVS1-To-KDS1-Stream-Processor'
client = boto3.client('rekognition')

response = client.stop_stream_processor(
    Name=STREAM_PROCESSOR_NAME
)
