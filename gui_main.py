import cv2
import numpy as np
import threading
import json
import Queue
import random
import math
import time
import Tkinter
import tkMessageBox
import tkFont
from PIL import Image
from PIL import ImageTk
from os import listdir, path, makedirs, remove

from class_ArduinoSerMntr import*
from class_CameraMntr import*
import class_ImageProcessing

class App:
    # Ininitalization
    def __init__(self,root):
        self.ArdMntr= MonitorThread()
        self.ArdMntr.start()
        
        self.CamMntr= CameraLink()

        myfont14 = tkFont.Font(family="Verdana", size=14)
        myfont12 = tkFont.Font(family="Verdana", size=12)
        myfont10 = tkFont.Font(family="Verdana", size=10)
        '''
        self.root = Tkinter.Tk()
        self.root.title("[Arduino] Stepper Control")
        self.root.attributes('-zoomed', True) # FullScreen
        '''
        self.root= root
        # ====== Parameters ================================
        self.savePath= 'Data/'
        self.saveParaPath= 'Data/Para/'
        self.configName= 'conifg.json'
        params= self.get_params(self.saveParaPath, self.configName)
        self.threshold_graylevel= params["plastic_thrshd_gray"]
        self.threshold_size= params["plastic_thrshd_size"] 
        self.scan_X= params["Scan_X (Beg,Interval,Amount)"]
        self.scan_Y= params["Scan_Y (Beg,Interval,Amount)"]
        self.limit= params["limit Maximum (X,Y)"]
        
        self.imageProcessor= class_ImageProcessing.contour_detect(self.savePath,self.saveParaPath)
        #self.mode= 0
        self.drawing= False
        self.x1, self.y1, self.x2, self.y2= -1,-1,-1,-1        
        self.StartScan_judge= False
        #self.cap_scanning= False
        self.saveScanning= 'XXX'
        '''
        self.scan_X= [0, 500, 4] #[beg, interval, amount]
        self.scan_Y= [0, 500, 3] #[beg, interval, amount]
        self.limit= [8000, 9500] #[X,Y]
        self.threshold_graylevel= 128
        self.threshold_size= 20
        '''
        self.screen_width, self.screen_height= self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        #self.screen_width, self.screen_height = width, height
        btn_width, btn_height= 15, 1
        self.interval_x, self.interval_y= 6, 6
        #print width,',', height,' ; ',btn_width,',', btn_height
        
        # ====== [Config] Menu Bar============
        self.menubar= Tkinter.Menu(self.root)
        self.FileMenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File",underline=0, menu=self.FileMenu)
        self.FileMenu.add_command(label="Save Image", command=self.btn_saveImg_click)
        self.ConnectMenu = Tkinter.Menu(self.menubar, tearoff=0)
        self.ConnectMenu.add_command(label="Connect to Arduino", command=self.set_ArdConnect)
        self.menubar.add_cascade(label="Communcation", underline= 0, menu=self.ConnectMenu)
        self.ImgProcess= Tkinter.Menu(self.menubar, tearoff=0)
        self.ImgProcess.add_command(label="Set Background", command= self.plastic_set_background)
        self.ImgProcess.add_command(label='Detect Scratch', command= self.plastic_detect_scratch)
        self.menubar.add_cascade(label="Image Processing", underline=0, menu= self.ImgProcess)
        self.root.config(menu= self.menubar)
        self.root.update()
        # ====== [Config] Current position of motor ===========
        self.lbl_CurrCoord= Tkinter.Label(self.root, text="[ Current Position ]",     font= myfont14)
        self.lbl_CurrCoord.place(x= self.interval_x, y= self.interval_y)
        self.root.update()
        self.lbl_CurrPos= Tkinter.Label(self.root, text="(X, Y)= (-1, -1)",font= myfont12)
        self.lbl_CurrPos.place(x= self.interval_x, y= self.lbl_CurrCoord.winfo_y()+ self.lbl_CurrCoord.winfo_height())
        self.root.update()
        #======[Step Motor Control] ========
        self.lbl_MoveCoord= Tkinter.Label(self.root, text="[ Step Motor Control ]", font= myfont14)
        self.lbl_MoveCoord.place(x= self.interval_x, y= self.lbl_CurrPos.winfo_y()+ self.lbl_CurrPos.winfo_height()+self.interval_y)
        self.root.update()

        self.lbl_Xpos= Tkinter.Label(self.root, text= 'X :',font= myfont12)
        self.lbl_Xpos.place(x= self.interval_x, y = self.lbl_MoveCoord.winfo_y()+ self.lbl_MoveCoord.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_Xpos= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_Xpos.insert(Tkinter.END, "0")
        self.entry_Xpos.place(x= self.lbl_Xpos.winfo_x()+ self.lbl_Xpos.winfo_width(), y= self.lbl_Xpos.winfo_y())
        self.root.update()
        self.lbl_Ypos= Tkinter.Label(self.root, text= 'Y :',font= myfont12)
        self.lbl_Ypos.place(x= self.entry_Xpos.winfo_x()+ self.entry_Xpos.winfo_width()+ self.interval_x, y = self.lbl_Xpos.winfo_y())
        self.root.update()
        self.entry_Ypos= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_Ypos.insert(Tkinter.END, "0")
        self.entry_Ypos.place(x= self.lbl_Ypos.winfo_x()+ self.lbl_Ypos.winfo_width(), y= self.lbl_Ypos.winfo_y())
        self.root.update()
        self.lbl_posUnit= Tkinter.Label(self.root, text='(step)')
        self.lbl_posUnit.place(x= self.entry_Ypos.winfo_x()+ self.entry_Ypos.winfo_width(), y= self.entry_Ypos.winfo_y()+self.interval_y)

        self.btn_MoveTo= Tkinter.Button(self.root, text= 'Move to', command= self.btn_MoveTo_click,font= myfont14)
        self.btn_MoveTo.place(x= self.lbl_Xpos.winfo_x(), y=self.lbl_Ypos.winfo_y()+ self.lbl_Ypos.winfo_height()+ self.interval_y)
        self.root.update()


        #======[Scanning Control] ========
        self.lbl_Scan= Tkinter.Label(self.root, text="[ Scanning Control ]", font= myfont14)
        self.lbl_Scan.place(x= self.interval_x, y= self.btn_MoveTo.winfo_y()+ self.btn_MoveTo.winfo_height()+self.interval_y)
        self.root.update()

        self.lbl_Scan1stPt= Tkinter.Label(self.root, text= 'Start point (X, Y):',font= myfont12)
        self.lbl_Scan1stPt.place(x= self.interval_x, y = self.lbl_Scan.winfo_y()+ self.lbl_Scan.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_1stXpos= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_1stXpos.insert(Tkinter.END, '{0}'.format(self.scan_X[0]))
        self.entry_1stXpos.place(x= self.lbl_Scan1stPt.winfo_x(), y= self.lbl_Scan1stPt.winfo_y()+ self.lbl_Scan1stPt.winfo_height())
        self.root.update()

        self.lbl_Scan1stPt_comma= Tkinter.Label(self.root, text= ', ', font= myfont12)
        self.lbl_Scan1stPt_comma.place(x=self.entry_1stXpos.winfo_x()+self.entry_Xpos.winfo_width(), y= self.entry_1stXpos.winfo_y())
        self.root.update()

        self.entry_1stYpos= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_1stYpos.insert(Tkinter.END, '{0}'.format(self.scan_Y[0]))
        self.entry_1stYpos.place(x= self.lbl_Scan1stPt_comma.winfo_x()+self.lbl_Scan1stPt_comma.winfo_width(), y= self.lbl_Scan1stPt_comma.winfo_y())
        self.root.update()
       
        self.lbl_ScanInterval= Tkinter.Label(self.root, text='Interval (X, Y) :', font= myfont12)
        self.lbl_ScanInterval.place(x= self.entry_1stXpos.winfo_x(), y= self.entry_1stXpos.winfo_y()+ self.entry_1stXpos.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_ScanInterval_X= Tkinter.Entry(self.root, font=myfont12, width=4)
        self.entry_ScanInterval_X.insert(Tkinter.END, '{0}'.format(self.scan_X[1]))
        self.entry_ScanInterval_X.place(x= self.lbl_ScanInterval.winfo_x(), y= self.lbl_ScanInterval.winfo_y()+self.lbl_ScanInterval.winfo_height())
        self.root.update()
        self.lbl_ScanInterval_comma= Tkinter.Label(self.root, text= ', ', font= myfont12)
        self.lbl_ScanInterval_comma.place(x=self.entry_ScanInterval_X.winfo_x()+self.entry_ScanInterval_X.winfo_width(), y= self.entry_ScanInterval_X.winfo_y())
        self.root.update()
        self.entry_ScanInterval_Y= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_ScanInterval_Y.insert(Tkinter.END, '{0}'.format(self.scan_Y[1]))
        self.entry_ScanInterval_Y.place(x= self.lbl_ScanInterval_comma.winfo_x()+self.lbl_ScanInterval_comma.winfo_width(), y= self.lbl_ScanInterval_comma.winfo_y())
        self.root.update()


        self.lbl_ScanAmount= Tkinter.Label(self.root, text='Scanning Step (X, Y) :', font= myfont12)
        self.lbl_ScanAmount.place(x= self.entry_ScanInterval_X.winfo_x(), y= self.entry_ScanInterval_X.winfo_y()+ self.entry_ScanInterval_X.winfo_height()+self.interval_y)
        self.root.update()
        self.entry_ScanAmount_X= Tkinter.Entry(self.root, font=myfont12, width=4)
        self.entry_ScanAmount_X.insert(Tkinter.END, '{0}'.format(self.scan_X[2]))
        self.entry_ScanAmount_X.place(x= self.lbl_ScanAmount.winfo_x(), y= self.lbl_ScanAmount.winfo_y()+self.lbl_ScanAmount.winfo_height())
        self.root.update()
        self.lbl_ScanAmount_comma= Tkinter.Label(self.root, text= ', ', font= myfont12)
        self.lbl_ScanAmount_comma.place(x=self.entry_ScanAmount_X.winfo_x()+self.entry_ScanAmount_X.winfo_width(),y= self.entry_ScanAmount_X.winfo_y())
        self.root.update()
        self.entry_ScanAmount_Y= Tkinter.Entry(self.root, font= myfont12, width=4)
        self.entry_ScanAmount_Y.insert(Tkinter.END, '{0}'.format(self.scan_Y[2]))
        self.entry_ScanAmount_Y.place(x= self.lbl_ScanAmount_comma.winfo_x()+self.lbl_ScanAmount_comma.winfo_width(), \
                                      y= self.lbl_ScanAmount_comma.winfo_y())
        self.root.update()

        self.btn_StartScan= Tkinter.Button(self.root, text= 'Start Scan', command= self.btn_StartScan_click,font= myfont14, fg= 'green', width= btn_width, height= btn_height)
        self.btn_StartScan.place(x= self.entry_ScanAmount_X.winfo_x(), y=self.entry_ScanAmount_X.winfo_y()+ self.entry_ScanAmount_X.winfo_height()+ self.interval_y)
        self.root.update()
        # ===== Plastic Detection =======
        self.lbl_scracth_detect= Tkinter.Label(self.root, text="[ Detection Setting ]", font= myfont14)
        self.lbl_scracth_detect.place(x= self.interval_x, y= self.btn_StartScan.winfo_y()+ self.btn_StartScan.winfo_height()+self.interval_y)
        self.root.update()
        
        self.scale_threshold_graylevel = Tkinter.Scale(self.root , from_= 0 , to = 255 , orient = Tkinter.HORIZONTAL , label = "(Unused) threshold of gray_level", font = myfont12, width = 10, length = 200 )
        self.scale_threshold_graylevel.set(self.threshold_graylevel)
        self.scale_threshold_graylevel.place(x= self.lbl_scracth_detect.winfo_x(), y= self.lbl_scracth_detect.winfo_y()+ self.lbl_scracth_detect.winfo_height())
        self.scale_threshold_graylevel.config(state= 'disabled')
        self.root.update()

        self.scale_threshold_size = Tkinter.Scale(self.root , from_ = 0 , to = 500 , orient = Tkinter.HORIZONTAL , label = "threshold of defect_size", font = myfont12, width = 10, length = 200 )
        self.scale_threshold_size.set(self.threshold_size)

        self.scale_threshold_size.place(x= self.scale_threshold_graylevel.winfo_x(), y= self.scale_threshold_graylevel.winfo_y()+ self.scale_threshold_graylevel.winfo_height())
        self.root.update()

        self.btn_saveImg= Tkinter.Button(self.root, text='Save Image', command= self.btn_saveImg_click,font= myfont14, width= btn_width, height= btn_height)
        self.btn_saveImg.place(x= self.lbl_MoveCoord.winfo_x(), y= self.screen_height-self.FileMenu.winfo_reqheight()-self.btn_MoveTo.winfo_reqheight()-self.interval_y*6)
        self.root.update()
        
        self.btn_detect= Tkinter.Button(self.root, text='Otsu Binary', command= self.plastic_detect_scratch,font= myfont14, width= btn_width, height= btn_height)
        self.btn_detect.place(x= self.lbl_MoveCoord.winfo_x(), y= self.btn_saveImg.winfo_y()- self.btn_saveImg.winfo_height()- self.interval_y)
        self.root.update()
        
        # ===== Main Image Frame ======
        self.frame_width, self.frame_height= int(0.5*(self.screen_width-self.lbl_MoveCoord.winfo_width()- (self.interval_x*11))), int(0.5*(self.screen_height-self.FileMenu.winfo_reqheight()-self.interval_y*6))
        
        #self.frame_width, self.frame_height= self.screen_width-self.lbl_MoveCoord.winfo_width()- (self.interval_x*11), self.screen_height-self.FileMenu.winfo_reqheight()-self.interval_y*6
        self.frame= np.zeros((int(self.frame_height), int(self.frame_width),3),np.uint8)
        #frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
        result = Image.fromarray(self.frame)
        result = ImageTk.PhotoImage(result)
        self.panel = Tkinter.Label(self.root , image = result)
        self.panel.image = result
        self.panel.place(x=self.lbl_MoveCoord.winfo_width()+ self.interval_x*2, y= 0)
        self.root.update()
        # ====== Display merge Image Frame =====
        self.mergeframe_width, self.mergeframe_height= self.frame_width, self.frame_height*2+2
        self.mergeframe= np.zeros((int(self.mergeframe_height), int(self.mergeframe_width),3),np.uint8)
        #frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
        cv2.putText(self.mergeframe, 'Display Scanning Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
        result = Image.fromarray(self.mergeframe)
        result = ImageTk.PhotoImage(result)
        self.panel_mergeframe = Tkinter.Label(self.root , image = result)
        self.panel_mergeframe.image = result
        self.panel_mergeframe.place(x=self.panel.winfo_x()+ self.panel.winfo_width(), y= 0)
        self.root.update()
        # ====== One Shot Image Frame ======
        self.singleframe_width, self.singleframe_height= self.frame_width, self.frame_height
        self.singleframe= np.zeros((int(self.singleframe_height), int(self.singleframe_width),3),np.uint8)
        cv2.putText(self.singleframe, '1 shot Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)
        result = Image.fromarray(self.singleframe)
        result = ImageTk.PhotoImage(result)
        self.panel_singleframe = Tkinter.Label(self.root , image = result)
        self.panel_singleframe.image = result
        self.panel_singleframe.place(x=self.panel.winfo_x(), y= self.panel.winfo_y()+ self.panel.winfo_height())
        self.root.update()
        
        # ====== UI callback setting ======
        self.panel.after(50, self.check_frame_update)
        self.lbl_CurrPos.after(5, self.UI_callback)
        # ====== Override CLOSE function ==============
        self.root.protocol('WM_DELETE_WINDOW',self.on_exit)
        # ====== Thread ========
        self.main_run_judge= True
        self.thread_main= threading.Thread(target= self.main_run)
        self.thread_main.start() 
        self.scanning_judge= True
        self.thread_scanning= threading.Thread(target= self.scanning_run)
        self.thread_scanning.start()

    def get_params(self , arg_filepath, arg_filename):
        if path.isfile(arg_filepath+arg_filename):
            with open(arg_filepath+arg_filename , 'r') as file_pointer:
                data = json.load(file_pointer)
        else:
            data= dict()
            data["plastic_thrshd_gray"] = 128
            data["plastic_thrshd_size"] = 20
            data["Scan_X (Beg,Interval,Amount)"]= [0, 500, 4]
            data["Scan_Y (Beg,Interval,Amount)"]= [0, 500, 4]
            data["limit Maximum (X,Y)"]= [8000, 95000]
        return data

    def store_para(self, arg_filepath, arg_filename):
        # make sure output dir exists
        if(not path.isdir(self.saveParaPath)):
            makedirs(arg_savePath)
        data = dict()
        data["plastic_thrshd_gray"] = self.scale_threshold_graylevel.get()
        data["plastic_thrshd_size"] = self.scale_threshold_size.get()
        data["Scan_X (Beg,Interval,Amount)"]= [int(self.entry_1stXpos.get()), int(self.entry_ScanInterval_X.get()), int(self.entry_ScanAmount_X.get())]
        data["Scan_Y (Beg,Interval,Amount)"]= [int(self.entry_1stYpos.get()), int(self.entry_ScanInterval_Y.get()), int(self.entry_ScanAmount_Y.get())]
        data["limit Maximum (X,Y)"]= self.limit
        with open(arg_filepath+arg_filename , 'w') as out:
            json.dump(data , out)
        print "Para set"

    # Override CLOSE function
    def on_exit(self):
        #When you click to exit, this function is called
        if tkMessageBox.askyesno("Exit", "Do you want to quit the application?"):
            self.store_para(self.saveParaPath, self.configName)
            print 'Close Main Thread...'
            self.main_run_judge= False
            self.ArdMntr.exit= True
            self.scanning_judge= False
            self.CamMntr.stop_clean_buffer()
            del(self.thread_main)
            print 'Close Arduino Thread...'
            del(self.CamMntr.thread_clean_buffer)
            print 'Close Scanning Thread...'
            del(self.thread_scanning)
            self.root.destroy()

    def UI_callback(self):
        if self.ArdMntr.connect== True:
            tmp_text= '(X, Y)= ('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+')'
        else:
            tmp_text='Arduino Connection Refuesed!'

        self.lbl_CurrPos.config(text= tmp_text)
        self.lbl_CurrPos.after(10,self.UI_callback)
    
    def Lock_UI(self, arg_Lock):
        if arg_Lock:
            self.btn_MoveTo.config(state= 'disabled')
            self.entry_Xpos.config(state= 'disabled')
            self.entry_Ypos.config(state= 'disabled')
            self.btn_detect.config(state= 'disabled')
            self.btn_saveImg.config(state= 'disabled')
            self.entry_1stXpos.config(state= 'disabled')
            self.entry_1stYpos.config(state= 'disabled')
            self.entry_ScanInterval_X.config(state= 'disabled')
            self.entry_ScanInterval_Y.config(state= 'disabled')
            self.entry_ScanAmount_X.config(state= 'disabled')
            self.entry_ScanAmount_Y.config(state= 'disabled')
        else:
            self.btn_MoveTo.config(state= 'normal')
            self.entry_Xpos.config(state= 'normal')
            self.entry_Ypos.config(state= 'normal')
            self.btn_detect.config(state= 'normal')
            self.btn_saveImg.config(state= 'normal')
            self.entry_1stXpos.config(state= 'normal')
            self.entry_1stYpos.config(state= 'normal')
            self.entry_ScanInterval_X.config(state= 'normal')
            self.entry_ScanInterval_Y.config(state= 'normal')
            self.entry_ScanAmount_X.config(state= 'normal')
            self.entry_ScanAmount_Y.config(state= 'normal')

    def plastic_set_background(self):
        frame= self.CamMntr.get_frame()
        self.imageProcessor.set_background(frame)

    def plastic_detect_scratch(self):
        print 'Start Detect'
        #result= self.CamMntr.subract_test()
        self.imageProcessor.set_threshold_size(int(self.scale_threshold_size.get()))
        self.imageProcessor.set_threshold_graylevel(int(self.scale_threshold_graylevel.get()))
        result= self.imageProcessor.get_contour(self.singleframe, True, self.savePath, 'Plastic_ScracthDetect.png')
        self.display_panel_singleframe(result)

    def set_ArdConnect(self):
        self.ArdMntr.connect_serial()

    def set_frame(self, frame):
        self.frame= frame
    
    def display_panel_singleframe(self, arg_frame):
        tmp_frame= cv2.cvtColor(arg_frame, cv2.COLOR_BGR2RGB)
        #tmp_frame = self.mark_cross_line(tmp_frame)
	tmp_frame= cv2.resize(tmp_frame,(self.singleframe_width,self.singleframe_height),interpolation=cv2.INTER_LINEAR)
        result = Image.fromarray(tmp_frame)
        result = ImageTk.PhotoImage(result)
        self.panel_singleframe.configure(image = result)
        self.panel_singleframe.image = result

    def reset_mergeframe(self):
        self.mergeframe= np.zeros((int(self.mergeframe_height), int(self.mergeframe_width),3),np.uint8)
        cv2.putText(self.mergeframe, 'Display Scanning Result',(10,20),cv2.FONT_HERSHEY_SIMPLEX, 0.5,(255,255,255),1)

    def set_mergeframe_size(self, arg_x, arg_y):
        self.mergeframe_splitX= int((self.mergeframe_width-self.interval_x*2)/arg_y)
        self.mergeframe_splitY= int((self.mergeframe_height-100)/arg_x)
    
    def display_panel_mergeframe(self, arg_frame, arg_stepX, arg_stepY): 
        tmp_frame= cv2.cvtColor(arg_frame, cv2.COLOR_BGR2RGB)
        tmp_frame= cv2.resize(tmp_frame,(self.mergeframe_splitX,self.mergeframe_splitY),interpolation=cv2.INTER_LINEAR)
        begX= self.interval_x+self.mergeframe_splitX*arg_stepX
        begY= 50+ self.mergeframe_splitY* arg_stepY 
        begY= self.mergeframe_height- 50- self.mergeframe_splitY*arg_stepY
        self.mergeframe[begY-self.mergeframe_splitY:begY, begX: begX+ self.mergeframe_splitX]= tmp_frame
        print '>> mergeframe_splitY, splitX= ', self.mergeframe_splitY, ', ', self.mergeframe_splitX
        print '>> tmp_frame.shape[0,1]= ', tmp_frame.shape[0],', ',tmp_frame.shape[1]
        
        result = Image.fromarray(self.mergeframe)
        result = ImageTk.PhotoImage(result)
        self.panel_mergeframe.configure(image = result)
        self.panel_mergeframe.image = result

    def btn_StartScan_click(self):
        self.imageProcessor.set_threshold_size(int(self.scale_threshold_size.get()))
        self.imageProcessor.set_threshold_graylevel(int(self.scale_threshold_graylevel.get()))
        print 'Start'
        if self.StartScan_judge:
            self.StartScan_judge= False
            self.Lock_UI(True)
            self.btn_StartScan.config(text= 'Start Scan', fg='green')
        else:
            if self.ArdMntr.connect:
                try:
                    self.reset_mergeframe()
                    self.scan_X= [int(self.entry_1stXpos.get()), int(self.entry_ScanInterval_X.get()), int(self.entry_ScanAmount_X.get())]
                    self.scan_Y= [int(self.entry_1stYpos.get()), int(self.entry_ScanInterval_Y.get()), int(self.entry_ScanAmount_Y.get())]
                    self.set_mergeframe_size(self.scan_X[2], self.scan_Y[2])
                    self.reset_mergeframe()
                    #print '### ', self.scan_X, self.scan_Y
                
                    cmd= 'G00 X{0} Y{1}'.format(self.scan_X[0], self.scan_Y[0])
                    self.ArdMntr.serial_send(cmd)
                    if self.scan_X[0]+self.scan_X[1]*self.scan_X[2]<self.limit[0] | self.scan_Y[0]+self.scan_Y[1]*self.scan_Y[2]<self.limit[1]:
                        print 'scanning...'
                        self.StartScan_judge= True
                    	self.Lock_UI(True)
                    	self.btn_StartScan.config(text= 'STOP Scan', fg='red')
                    else:
                        tkMessageBox.showerror("Error", "The scanning of X should be in [0~{0}]\nThe range of Y should be in [0~{1}]".format(self.limit[0],self.limit[1]))
                except:
                    tkMessageBox.showerror('Error', 'Please enter nubmer')
            else:
                tkMessageBox.showerror("Error", "Arduino connection refused!")


    def btn_saveImg_click(self):
        #self.saveImg= True
        #self.Lock_UI(False)
        self.singleframe = self.CamMntr.get_frame()
        self.saveImg_function(self.singleframe, self.savePath, 'Frame1')
        self.display_panel_singleframe(self.singleframe)


    def btn_MoveTo_click(self):
        if self.ArdMntr.connect:
            try:
                Target_X= int(self.entry_Xpos.get())
                Target_Y= int(self.entry_Ypos.get())
                if (Target_X>=0) & (Target_X<=self.limit[0]) & (Target_Y>=0) & (Target_Y<=self.limit[1]):
                    cmd= 'G00 X{0} Y{1}'.format(Target_X, Target_Y)
                    self.ArdMntr.serial_send(cmd)
                    print 'Command: ', cmd
                    time.sleep(1)                
                else:
                    tkMessageBox.showerror("Error", "The range of X should be in [0~{0}]\nThe range of Y should be in [0~{1}]".format(self.limit[0],self.limit[1]))
            
            except:
                tkMessageBox.showerror("Error", "Please enter number!")
        else:
            tkMessageBox.showerror("Error", "Arduino connection refused!")

    def mark_cross_line(self , frame):
        w = frame.shape[0] / 2
        h = frame.shape[1] / 2
        cv2.line(frame , (h - 15 , w) , (h + 15 , w) , (255 , 0 , 0) , 1)
        cv2.line(frame , (h , w - 15) , (h , w + 15) , (255 , 0 , 0) , 1)
        return frame

    def saveImg_function(self, arg_frame,arg_savePath, arg_filename):
        # make sure output dir exists
        if(not path.isdir(arg_savePath)):
            makedirs(arg_savePath)
        #tmp= cv2.cvtColor(arg_frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(arg_savePath+arg_filename+'.jpg',arg_frame)
    
    def scanning_run(self):
        step=0
        while self.scanning_judge:
            if self.StartScan_judge:
                print 'Scanning...'
                if not(self.imageProcessor.check_background()):
                    tkMessageBox.showerror("Error", 'Background has not been built yet!')
                    self.StartScan_judge= False
                    break
                for step_X in range(0, self.scan_X[2]):
                    for step_Y in range(0, self.scan_Y[2]):
                        if self.StartScan_judge== False:
                            break
                        if step_X % 2 ==0:
                            tmp_step_Y= step_Y
                        else:
                            tmp_step_Y= self.scan_Y[2]- step_Y-1
                        tmp_X, tmp_Y= self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ tmp_step_Y*self.scan_Y[1]
                        #tmp_X, tmp_Y= self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ step_Y*self.scan_Y[1]
                        print 'X, Y: ', tmp_X, ', ', tmp_Y
                        #self.saveScanning= 'Raw_{0}_{1}.png'.format(self.scan_X[0]+ step_X*self.scan_X[1], self.scan_Y[0]+ step_Y*self.scan_Y[1])
                        cmd= 'G00 X{0} Y{1}'.format(tmp_X, tmp_Y)
                        self.ArdMntr.serial_send(cmd)
                        time.sleep(1)
                        while 1:
                            if (self.ArdMntr.cmd_state.is_ready()):
                                time.sleep(1)
                                #self.cap_scanning= True
                                self.saveScanning= '{0}_'.format(step)+self.ArdMntr.cmd_state.strCurX+'_'+self.ArdMntr.cmd_state.strCurY
                                frame= self.CamMntr.get_frame()
                                self.saveImg_function(frame, self.savePath+'Scanning/','Raw_'+self.saveScanning)
                                result= self.imageProcessor.get_contour(frame, True, self.savePath+'Scanning/', 'Detect_'+self.saveScanning)
                                self.display_panel_singleframe(result)
                                #self.display_panel_mergeframe(result, step_X, step_Y)
                                #self.display_panel_mergeframe(result, step_Y, step_X)
                                self.display_panel_mergeframe(result, tmp_step_Y, step_X)
                                
                                print self.saveScanning
                                #time.sleep(2)
                                break
                            else:
                                time.sleep(1)
                        if self.StartScan_judge== False:
                            break
                        step= step+1
                self.StartScan_judge= False
                self.Lock_UI(False)
                self.btn_StartScan.config(text= 'Start Scan', fg='green')
            else:
                time.sleep(0.2)
                step=0      


    def check_frame_update(self):
        result = Image.fromarray(self.frame)
        result = ImageTk.PhotoImage(result)
        self.panel.configure(image = result)
        self.panel.image = result
        self.panel.after(8, self.check_frame_update)

    def main_run(self):
        while self.main_run_judge:
            frame= self.CamMntr.get_frame()
            frame= cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = self.mark_cross_line(frame)
	    frame= cv2.resize(frame,(self.frame_width,self.frame_height),interpolation=cv2.INTER_LINEAR)
            text='Arduino Connection Refused ...'
            color= (0,0,0)
            if self.ArdMntr.connect== True:
                if self.StartScan_judge == False:
                    if self.ArdMntr.cmd_state.is_ready():
                        text= 'Idling ...'
                        color = (0 , 255 , 0)
                    else:
                        text= 'Moving ...'
                        color = (255,0,0)
                else:
                    if self.ArdMntr.cmd_state.is_ready():
                        text= 'Processing...'
                        color = (0 , 255 , 0)
                    else:
                        text= 'Scanning...'+'(X, Y)= ('+self.ArdMntr.cmd_state.strCurX+', '+self.ArdMntr.cmd_state.strCurY+')'
                        color = (255,0,0)
            cv2.putText(frame, text,(10,40),cv2.FONT_HERSHEY_SIMPLEX, 0.7,color,1)

            self.set_frame(frame)
            time.sleep(0.01)

root = Tkinter.Tk()
root.title("[Arduino] Stepper Control")
root.attributes('-zoomed', True) # FullScreen
app= App(root)
root.mainloop()
