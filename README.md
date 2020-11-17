# Smart Door
### A cloud-based video facial recognition authentication service for homeowners

**Teammates:** [Theodore Hadges](https://github.com/theodorehadges), and [Caroline Barker](https://github.com/CarolineNB), and [Aravind Vaddi](https://github.com/aravindvaddi)

Inspired by the Ring Home Security system, this implementation has the added feature of automatically granting access to previously authenticated users (by analyzing visitors faces and storing classifications) 

This is a purely cloud-based (AWS) system, save for the simple front-end pages and the hardware required to trigger the video stream.

## Table of Contents
1. [Demo](#demo-and-overview)
2. [Architecture Overview](#architecture-overview)
    - [Auto-Deployment](#auto-deployment)
    - [Full Architecture Diagram](#full-architecture-diagram)
3. [Indvidual Components](#individual-components)
    - [Hardware](#hardware)
    - [Stream Processor](#stream-processor)
    - [S3](#s3)
    - [CloudFront](#cloudfront)
    - [Front-end](#front-end)
    - [API Gateway](#api-gateway)
    - [Lambda LF0](#lambda-lf0)
    - [Rekognition](#rekognition)
    - [Lambda LF1](#lambda-lf1)
    - [SNS](#sns)
    - [Lambda LF2](#lambda-lf2)
    - [DynamoDB](#dynamodb)
    - [Cognito](#cognito)
    

## Demo and overview
Below, a demo which simulates a visitor walking up to the house and triggering the motion sensor. (This is only
the beginning of the process.)
I trigger the partial infrared (PIR) motion sensor with my hand, but obviously it would be facing the same direction as the camera
in real life.  Once motion is detected, the camera module begins streaming to our stream processor in the cloud.
When we view the Kinesis Video Stream (the first stage of the processor) monitor below, you'll notice my face is displayed
after a few seconds of the stream being triggered.  
<img src="https://github.com/theodorehadges/smart-door/blob/main/media/motion-sensor-demo.gif" width="70%" />

What happens next is conditional and depends on whether the visitor (me in this cas) is a new or returning (approved) visitor.

#### If new visitor:
If they are a new visitor, a notification will be sent to the homeowner via SNS in the form of a text message.
The owner, upon clicking the link in the text message, will be led to a page like this:
<img src="https://github.com/theodorehadges/smart-door/blob/main/media/visitor-verification.png" width="70%" />

Note that the owner must login before being able to access this page and view visitor images.

Next, if the owner approves the visitor, the visitor's face will be indexed using Rekognition so that 
the system will be able to detect that particular visitor an automatically grant them access in the future,
without the need for the owner's approval. 

The visitor will then receive a text with a sign-in link and a one-time-password (OTP) which expires in 5 minutes.
The sign-in form looks like this:  
<img src="https://github.com/theodorehadges/smart-door/blob/main/media/wp2.png" width="70%" />

If the OTP is correct then the user will be granted access. At this point the door would be physically unlocked,
but that is not the focus of this project, so instead the user is redirected to the welcome page:  

<img src="https://github.com/theodorehadges/smart-door/blob/main/media/welcome.gif" width="70%" />

However, if the user is denied, they'll be redirected to the denied page. (In this case, the door would remain locked.)  
<img src="https://github.com/theodorehadges/smart-door/blob/main/media/denied.gif" width="70%" />

#### If returning visitor:
Since the owner already approved this visitor, the visitor's face details are stored in our Rekognition collection and database.
If that visitor returns, we perform facial analysis again, capture a frame of the video, and train the model by indexing
the new face and adding it to the same group as the previously indexed faces for this user.

The returning visitor gets a text message from the system with an OTP, and can login via the visitor page, as above.

## Architecture Overview

### Auto-Deployment
We used CodePipeline to auto-deploy code from our `master` branch on GitHub to S3. We also used the CloudFront content delivery network to distribute our
website and replicate the distribution configuration across multiple edge
locations around the world for caching content and providing fast delivery of
the website.  

Here is the flowchart for this process:  

<img src="https://github.com/theodorehadges/chatbot/blob/main/media/smart-door-codepipeline.png" />

### Full Architecture Diagram  

Here is the flowchart of our full architecture diagram.  
<img src="https://github.com/theodorehadges/chatbot/blob/main/media/architecture-diagram.png" />

There are a few services we haven't yet added to this diagram:
 - We used some S3 buckets for image storage and the front-end
 - We used Cognito so that the owner needs to login to the homeowner page (wp1).
 - We used CloudFront and CodePipeline as mentioned above
 - We used some hardware to sense motion and trigger a video stream to Kinesis

## Individual Components

### Hardware
<img src="https://github.com/theodorehadges/chatbot/blob/main/media/annotated-pi.png" />

#### Bill of Materials:
- Raspberry Pi 4
- Partial Infrared Sensor module with Fresnel lens
- Raspberry Pi Camera Video module
- Jumper wires

The program `if_motion_then_stream.py` takes care of the logic involved with detecting motion and
initiating the video stream.

Once the PIR sensor detects a certain amount of infrared light, it will send a HIGH signal to the 
corresponding GPIO pin on the Raspberry Pi in the form of a few volts. 

The sensor is a little sensitive and we don't want any false positives, so the system does not
begin streaming video until there are 10 consecutive time steps in which a HIGH signal is sent to the pin.
Each time step is 0.1 seconds.

Once this condition is met, the red LED will turn on, and the video will begin streaming to AWS Kinesis Video Stream,
the first step in our stream processor.

### Stream Processor
The stream processor is the pipeline through which our video data flows. There are three major components:
1. **Kinesis Video Stream (KVS):** This is the service which ingests the video stream which is sent from our camera module.
2. **Rekognition:** This is the service that performs video facial recognition analysis on all visitors.
3. **Kinesis Data Stream (KDS):** This is the service that captures and manages Rekognition output logs. This is the last step
in the pipeline, and we have set up a trigger from KDS to the Lambda LF1 function. LF1 is the consumer of this data.

### S3
* Created 2 main buckets: `smart-door-image-store` and `smart-door-b1`. 
* We put all frontend files in `smart-door-b1` and all images in `smart-door-image-store`.
* Added automatic deployment with CodePipeline as discussed in the next section.

### CodePipeline
The front-end is hosted in an S3 bucket. Since editing those files directly is impossible and downloading, editing, 
then reuploading is clumsy and inefficient, we decided to use CodePipeline. 
Whenever we push to our `master` branch in our GitHub repository, 
CodePipeline will pull those changes, then clone them to our S3 bucket. 
This makes for easy integration between GitHub and S3.

### CloudFront
The website source files are hosted on S3, but we also use a CDN called CloudFront to replicate configurations of the 
distribution to edge locations around the world, for caching content and providing fast delivery 
of the website.  

### Front-end
We built a very simple static website with approval/login forms. Website design and UX was not important for us. 
(We can always come back to this later.)

### API Gateway
- We built an API using API Gateway which allows us to make requests and get resources from our backend.

### Lambda LF0
* This is the Lambda function in the bottom of the architecture diagram. 
* Receives an event after the owner submits an approval form.
* If the new visitor is approved do the following:
    * Upload the image to S3
    * Index the face in Rekognition
    * Add the S3 object key to the `visitors` table
    * Generate an OTP for the new visitor and add it to the `passcodes` table
    * Send a text to the new visitor containing a sign-in link and the OTP
* Otherwise, if the visitor is denied access, do nothing.

### Rekognition

Rekognition is the second step in the stream processor pipeline (Kinesis Video Stream -> Rekognition -> Kinesis Data Stream).
When a visitor face matches a previously indexed face with at least 85% confidence, the current image of the 
visitor is indexed to train the model on this visitor. Here is what the response looks like when there is 
a person with ExternalImageID `ted-hadges` who has already visited twice:  

<img src="https://github.com/theodorehadges/chatbot/blob/main/media/matched-faces.png" />

### Lambda LF1
LF1 receives the video data stream event and does some checks. If the Rekognition response shows that there is a
matching face, then that user has already been approved in the past. Thus, LF1 at this point indexes the new face,
uploads the face to S3, adds the S3 object key to that user's `photos` list in the `visitors` table, then
sends a text message to the visitor with an OTP so that they can sign in.

Otherwise, if there is not a matching face, a text message will be sent to the owner. The owner, upon clicking
the link in the text and logging in via Cognito, will be presented with the image of the visitor and and 
an accept/deny form for the new user.

### SNS
We use AWS Simple Notification Service (SNS) for publishing text messages to users.

### Lambda LF2
LF2 is the lambda function at the top of the architecture diagram. All LF1 does is check whether the OTP 
of the returning visitor is valid and grant/deny them access. It also flags the OTP as having been used
and sets the expiration time for that OTP to the current time in the `passcodes` table.

### DynamoDB
There are two tables: `visitors` and `passcodes`. `visitors` has all information about visitors, while 
`passcodes` is only the visitor's phone number, their  OTP, and the expiration time.
We set a TTL for the `expTime` attribute of the `passcodes` table such that the record expires at that time.

### Cognito
As a fun add-on, we decided to add authentication. We created a userpool, and a new client app within that pool. 
Since the callback URL (where to redirect to once the user is signed in) must use https (not http), we used our CloudFront URL. 
We used an authorization code grant flow whereby the user receives a code via email upon registration and must enter the code on the screen to activate their account.

The only user who would need to make an account is the homeowner. Visitors would not be able to make an account; therefore the visitor login page is public.

Cognito has some nice built-in forms to handle registration and login. This is convenient in that we did not have to create a separate web page just for the form. 
