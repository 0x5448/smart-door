# Smart Door


### CLI commands to set up Rekognition
aws rekognition create-collection \
    --collection-id "collectionname"


### index an image
aws rekognition index-faces --image '{"S3Object":{"Bucket":"<S3BUCKET>","Name":"<MYFACE_KEY>.jpeg"}}' --collection-id "rekVideoBlog" --detection-attributes "ALL" --external-image-id "<YOURNAME>" --region us-east-1
