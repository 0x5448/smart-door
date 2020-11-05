gst-launch-1.0 -v v4l2src device=/dev/video2 ! videoconvert ! video/x-raw,format=I420,width=640,height=480,framerate=30/1 ! x264enc bframes=0 key-int-max=45 bitrate=500 tune=zerolatency ! video/x-h264,stream-format=avc,alignment=au ! kvssink stream-name="Assignment2-KVS1" storage-size=128 access-key="your-access-key" secret-key="your-secret-key"

