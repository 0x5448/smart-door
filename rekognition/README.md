# Stream processors connect KVS to Rekognition to KDS

### Stream processor controls (create/delete/start/stop)

Create:
`python3 create_stream_processor.py`

Delete:
`python3 delete_stream_processor.py`

Start:
`python3 start_stream_processor.py`

Stop:
`python3 stop_stream_processor.py`


### Useful CLI commands

List stream processors and status: 
`aws rekognition list-stream-processors`

If status is FAILED, use this to see what the problem is: 
`aws rekognition describe-stream-processor --name
KVS1-To-KDS1-Stream-Processor`


### Appendix
I added a custom policy called `stream-policy-for-KVS-read-and-KDS-write` for the `stream-processor-role` role since 
there were permission issues with the default policy.
