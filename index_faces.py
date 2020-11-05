# https://docs.aws.amazon.com/rekognition/latest/dg/API_IndexFaces.html


import boto3

#BUCKET = "amazon-rekognition"
BUCKET = "smart-door-image-store"
KEY = "ted_pic.jpg"  # Either key in S3 or however img frame gets passed from KVS
IMAGE_ID = KEY
COLLECTION = "faces"
REGION = "us-east-1"


# Collection is already created, but if it wasn't we can uncomment
# this to create it:
# rekognition.create_collection(CollectionId=COLLECTION)

def index_faces(bucket, key, collection_id, image_id=None, attributes=(), region=REGION):
    rekognition = boto3.client("rekognition", region)

    response = rekognition.index_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        ExternalImageId=image_id,
        DetectionAttributes=attributes,
    )

    return response['FaceRecords']


for record in index_faces(BUCKET, KEY, COLLECTION, IMAGE_ID):
    face = record['Face']
    #print(face)
    # details = record['FaceDetail']
    print("Face ({}%)".format(face['Confidence']))
    print("  FaceId: {}".format(face['FaceId']))
    print("  ImageId: {}".format(face['ImageId']))

"""
	Expected output:
	Face (99.945602417%)
	  FaceId: dc090f86-48a4-5f09-905f-44e97fb1d455
	  ImageId: f974c8d3-7519-5796-a08d-b96e0f2fc242
"""
