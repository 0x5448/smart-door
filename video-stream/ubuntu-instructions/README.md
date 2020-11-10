### Ubuntu Instructions
Follow these steps for Ubuntu 18.04:
1. Run `./get-dependencies.sh`
2. Follow these instructions (after running above script):  
https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp  
Note: might have to specify a C++ compiler if you're getting make errors. In
build/Makefile, add the following line in the environment section:  
`CXXFLAGS='-std=c++11' make target`
3. Run `gst-device-monitor-1.0` to make sure it was built correctly
4. Set environment variables for AWS creds and default region (you can see your own creds in
   `~/.aws/credentials`:
   - `export AWS_ACCESS_KEY_ID=YourAccessKeyId`
   - `export AWS_SECRET_ACCESS_ID=YourSecretAccessKeyId`
   - `export AWS_DEFAULT_REGION=us-east-1`
5. Run `timeout 12 ./start-streamer.sh`, and watch your beautiful self in the AWS Kinesis web console


#### Appendix
More Ubuntu instructions here:  
https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp
