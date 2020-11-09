import boto3

BUCKET = "smart-door-image-store"
COLLECTION = "faces"
REGION = "us-east-1"

rekognition = boto3.client("rekognition", REGION)

response = rekognition.delete_faces(
        CollectionId=COLLECTION,
        FaceIds=[
            "bd57edb5-526d-4315-82d2-a37f84673419"
            ]
        )
print(response)

