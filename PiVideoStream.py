# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2
import time

class PiVideoStream:
    def __init__(self, resolution=(256, 256), framerate=20, iso=800, sensormode=1, save_path = ""):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = (1,1)
        self.camera.shutter_speed = 60000000
        self.camera.iso = iso
        self.camera.sensor_mode = sensormode
        #self.camera.exposure_mode = 'off' 'fixedfps'
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="bgr", use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False
        self.save_path = save_path

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        #self.camera.start_recording("test.h264", format='rgb')
        if self.save_path:
                    self.camera.start_recording(self.save_path, format='rgb')
        for f in self.stream:
            start = time.time()
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)

            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                if self.save_path:
                                    self.camera.stop_recording()
                self.rawCapture.close()
                self.camera.close()
                return
            time.sleep(max(0.5/self.camera.framerate - (time.time() - start), 0.0))

    def read(self):
            # return the frame most recently read
            return self.frame
    def clearimg(self):
            self.frame = None
            return

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True
