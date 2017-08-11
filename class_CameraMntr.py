import threading
import json
import Queue
import random
import math
import time
import Tkinter
import tkMessageBox
import tkFont
import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

class CameraLink:
    def __init__(self):
        self.camera_id= [0, 1, 2, 3]
        self.clean_buffer_judge= True
        self.connect= False
        #self.cap= cv2.VideoCapture(self.camera_id)
        self.thread_clean_buffer= threading.Thread(target= self.clean_buffer) 
        self.thread_clean_buffer.start()

    def connect_camera(self):
        if not(self.connect):
            try:
                for tmp_id in self.camera_id:
                    try:
                        self.cap= cv2.VideoCapture(tmp_id)
                        print 'ID ',tmp_id,': connected successfully!'
                        self.connect= True
                        break
                    except:
                        print 'ID ',tmp_id,': connection Refused!'
            except:
                print 'Connection of Camera refused!'
                self.connect= False
                tkMessageBox.showerror("Error","Connection of Camera refused!")
        else:
            tkMessageBox.showerror("Error","Connection of Camera is already built!")

    def clean_buffer(self):
        while self.clean_buffer_judge:
            try: 
                tmp_frame= self.cap.grab()
            except:
                self.connect= False

    def stop_clean_buffer(self):
        self.clean_buffer_judge= False
    
    def get_frame(self):
        try:
            tmp_frame= self.cap.grab()
            _, tmp_frame= self.cap.retrieve()
        except:
            self.connect= False
        return tmp_frame

    def subract_test(self):
        tmp_frame= self.cap.grab()
        _, tmp_frame= self.cap.retrieve()
        plastic_golden= cv2.imread('Data/Para/background.png')
        test= cv2.subtract(tmp_frame, plastic_golden)
        return test 
