#from picamera.array import PiRGBArray
#from picamera import PiCamera
#following class is customised by me to set some camera parameters.
#It is originally part of imutils
import sys
sys.path.append('..')
from imutils.video import FPS
import numpy as np
import cv2
import imutils
import time
from datetime import datetime
from threading import *
import RPi.GPIO as GPIO
import cvui
import os
import picamera

#Following package is for tone generation
#run "sudo ./pwm" once after reboot(before using this)
#from PTPWMsin import PWM_Sin
from configparser import ConfigParser
import csv

config 		= ConfigParser()
config.read('config.ini')
cfg = 'raspicambehavior'
cfgDict = dict(config.items(cfg))
data_root 	= config.get(cfg, 'data_root')
image_stream_filename = config.get(cfg, 'raw_image_file')
res 	= list(map(int, config.get(cfg, 'resolution').split(', ')))
fr = int(config.get(cfg, 'framerate'))
iso = int(config.get(cfg, 'iso'))

summary_filename = data_root + os.sep +'expt_behavior_summary.csv'

rec_channel = 17

GPIO.setmode(GPIO.BCM)
# Setup your channel
GPIO.setup(rec_channel, GPIO.OUT)
GPIO.output(rec_channel, GPIO.LOW)

mouse_id = input("Please enter mouse ID: ")
sess_name = input("Session name (optional):")
data_root = data_root + os.sep + mouse_id + os.sep
if not os.path.exists(data_root):
    print("Creating data directory: ",data_root)
    os.makedirs(data_root)

WINDOW_NAME = 'Behavior recording'
#cvui.init(WINDOW_NAME)

summary_exists = os.path.isfile(summary_filename)
summaryfile = open (summary_filename, 'a', encoding="utf-8")
headers = [col.strip() for col in config.get(cfg, 'summary_header').split(',')]
writer = csv.DictWriter(summaryfile, delimiter=',', lineterminator='\n',fieldnames=headers)
if not summary_exists:
    writer.writeheader()  # file doesn't exist yet, write a header

# initialize the camera and grab a reference to the raw camera capture
camera = picamera.PiCamera()    # Setting up the camera
camera.resolution = (res[0],res[1])
camera.framerate = fr
#camera.awb_mode = 'off'
#camera.awb_gains = (1,1)
#camera.shutter_speed = 60000
#camera.sensor_mode = int(cfgDict['sensor_mode'])
# allow the camera to warmup
time.sleep(2)
camera.start_preview(fullscreen=False, window = (100, 50, res[0], res[1]))
while True:
    #image = vs.get_image()

    # To test the value of a pin use the .input method
    record_is_on = GPIO.input(rec_channel)  # Returns 0 if OFF or 1 if ON
    
    if record_is_on:
        # Get the current time and initialize the project folder
        tm = datetime.now()
        
        video_path = data_root + str(tm.year) + format(tm.month, '02d') + format(tm.day, '02d') + \
                           format(tm.hour, '02d') + format(tm.minute, '02d') + format(tm.second, '02d') + '_' + sess_name + '.h264'
        
        #image_hdf5_path = data_dir + os.sep + image_stream_filename
        #image_hdf5_file = tables.open_file(image_hdf5_path, mode='w')
        #data_storage = image_hdf5_file.create_earray(image_hdf5_file.root, 'raw_images',
        #                              tables.Atom.from_dtype(image.dtype),
        #                              shape=(0, res[0], res[1], 3))
        
        #video_writer= cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'XVID'), fr, (res[0],res[1]))
        camera.start_recording(video_path)
        #logFileName = data_dir + os.sep + "VideoTimestamp.txt"
        #logFile = open(logFileName, 'w', encoding="utf-8")
        #ogFile.write('frame' + '\t' + 'time' + '\n')
        print('Start recording\n\n\n')

        fps = FPS().start()
        while GPIO.input(rec_channel):
            start = time.time()
            #image = vs.get_image()
            fps.update()
            
            #data_storage.append(image[None])
            #video_writer.write(image)
            sttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            #logFile.write(str(fps._numFrames) + '\t' + sttime + '\n')

            #cvui.sparkline(combined, fpsHist, 0, 0, 400, 200);
            
            #cv2.imshow(WINDOW_NAME, image)
            #cvui.imshow(WINDOW_NAME, cv2.resize(image, (512, 512)));
            #k = cv2.waitKey(1)
            #if k == 27:
            #    break
            
            time.sleep(max(1.0/fr - (time.time() - start), 0))
            
        #image_hdf5_file.close()
        #video_writer.release()
        camera.stop_recording()
        #logFile.close()
        fps.stop()
        print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}\n\n".format(fps.fps()))
        writer.writerow({'mouse_id': mouse_id, 'data_path': video_path, 'start': fps._start, 'end': fps._end, 'fps': fps.fps()})

    #cvui.imshow(WINDOW_NAME, image);
    # Press Esc or Ctrl-C to stop the program
    k = cv2.waitKey(1)
    if k == 27:
        break
    #if cvui.button(image, 500, 530, "&Quit"):
    #    break
    
#vs.stop()
camera.stop_preview()
time.sleep(2)
run_threads = False

summaryfile.close()

#cv2.destroyAllWindows()
