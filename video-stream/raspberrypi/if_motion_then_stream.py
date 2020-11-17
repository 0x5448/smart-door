# This constantly polls the PIR sensor and prints 0 if no movement is detected and 1 otherwise.
# Since motion might be detected for a split second then not detected after, 
# this program only begins video streaming to Kinesis once 10 consecutive motion
# events have been detected (where an event is checked every 0.1 seconds).

# The red LED turns on once the video starts streaming to the cloud, and turns off when done.


import RPi.GPIO as GPIO
import time
from subprocess import call
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)         #Read output from PIR motion sensor
GPIO.setup(3, GPIO.OUT)         #LED output pin
print("pin 11: ", GPIO.input(11))

def motion_is_detected(count):
    count += 1
    if count is 10:
        print("Visitor detected. Initializing stream...")
        GPIO.output(3, 1)  #Turn ON LED
        time.sleep(0.5)
        call("timeout 12 ./start_streamer.sh", shell=True)
    return count 
        
def main():
    count = 0 # Consecutive times motion is sensed
    while True:
        i=GPIO.input(11)
        if i==0:                 #When output from motion sensor is LOW
            count = 0
            print("No visitors", i)
            GPIO.output(3, 0)  #Turn OFF LED
            time.sleep(0.1)
        elif i==1:               #When output from motion sensor is HIGH
            print("Motion detected", i)
            count = motion_is_detected(count)
            if count is 10:
                GPIO.output(3, 0)  #Turn OFF LED
                break 
            time.sleep(0.1)

if __name__ == "__main__":
    main()
