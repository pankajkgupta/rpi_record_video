#from picamera.array import PiRGBArray
#from picamera import PiCamera
#following class is customised by me to set some camera parameters.
#It is originally part of imutils
from PiVideoStream import PiVideoStream
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
import tables

#Following package is for tone generation
#run "sudo ./pwm" once after reboot(before using this)
#from PTPWMsin import PWM_Sin
from configparser import SafeConfigParser
import csv

config 		= SafeConfigParser()
config.read('config.ini')
cfg = config.get('configsection', 'config')
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

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(1,1))
kernel2 = np.ones((5,5),np.uint8)

mouse_id = input("Please enter mouse ID: ")

WINDOW_NAME = 'Behavior recording'
cvui.init(WINDOW_NAME)

summary_exists = os.path.isfile(summary_filename)
summaryfile = open (summary_filename, 'a', encoding="utf-8")
headers = ['mouse_id', 'data_path', 'start', 'end', 'fps']
writer = csv.DictWriter(summaryfile, delimiter=',', lineterminator='\n',fieldnames=headers)
if not summary_exists:
    writer.writeheader()  # file doesn't exist yet, write a header

# initialize the camera and grab a reference to the raw camera capture
vs = PiVideoStream(resolution=res, framerate=fr, iso=iso).start()
# allow the camera to warmup
time.sleep(2)

while True:
    image = vs.read()

    
    # To test the value of a pin use the .input method
    record_is_on = GPIO.input(rec_channel)  # Returns 0 if OFF or 1 if ON
    
    
    if record_is_on:
        # Get the current time and initialize the project folder
        tm = datetime.now()
        data_dir = data_root + str(tm.year) + format(tm.month, '02d') + format(tm.day, '02d') + \
                           format(tm.hour, '02d') + format(tm.minute, '02d') + format(tm.second, '02d')
        if not os.path.exists(data_dir):
            print("Creating data directory: ",data_dir)
            os.makedirs(data_dir)
        
        image_hdf5_path = data_dir + os.sep + image_stream_filename
        image_hdf5_file = tables.open_file(image_hdf5_path, mode='w')
        data_storage = image_hdf5_file.create_earray(image_hdf5_file.root, 'raw_images',
                                      tables.Atom.from_dtype(image.dtype),
                                      shape=(0, res[0], res[1], 3))
        logFileName = data_dir + os.sep + "VideoTimestamp.txt"
        logFile = open(logFileName, 'w', encoding="utf-8")
        logFile.write('frame' + '\t' + 'time' + '\n')
        print('Start recording')

        fps = FPS().start()
        while GPIO.input(rec_channel):
            start = time.time()
            image = vs.read()
            fps.update()
            
            data_storage.append(image[None])
            sttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            logFile.write(str(fps._numFrames) + '\t' + sttime + '\n')
            
            #cvui.sparkline(combined, fpsHist, 0, 0, 400, 200);
            
            #cv2.imshow("combined", combined)
            cvui.imshow(WINDOW_NAME, image);
            cv2.waitKey(1)
            
            time.sleep(max(1./fr - (time.time() - start), 0))
            
        image_hdf5_file.close()
        logFile.close()
        fps.stop()
        print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}\n\n".format(fps.fps()))
        writer.writerow({'mouse_id': mouse_id, 'data_path': data_dir, 'start': fps._start, 'end': fps._end, 'fps': fps.fps()})
    
    cvui.imshow(WINDOW_NAME, image);
    # Press Esc or Ctrl-C to stop the program
    k = cv2.waitKey(1)
    if k == 27:
        break
    #if cvui.button(image, 500, 530, "&Quit"):
    #    break
    
    
vs.stop()

time.sleep(2)
run_threads = False

summaryfile.close()

cv2.destroyAllWindows()

