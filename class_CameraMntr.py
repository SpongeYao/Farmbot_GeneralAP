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
        self.camera_id= 0
        self.clean_buffer_judge= True
        self.cap= cv2.VideoCapture(self.camera_id)
        self.thread_clean_buffer= threading.Thread(target= self.clean_buffer) 
        self.thread_clean_buffer.start()

    def clean_buffer(self):
        while self.clean_buffer_judge:
            tmp_frame= self.cap.grab()

    def stop_clean_buffer(self):
        self.clean_buffer_judge= False
    
    def get_frame(self):
        tmp_frame= self.cap.grab()
        _, tmp_frame= self.cap.retrieve()
        return tmp_frame

    def subract_test(self):
        tmp_frame= self.cap.grab()
        _, tmp_frame= self.cap.retrieve()
        plastic_golden= cv2.imread('Data/Para/background.png')
        test= cv2.subtract(tmp_frame, plastic_golden)
        return test 
