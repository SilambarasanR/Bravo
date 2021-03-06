import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
#from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout, 
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSlot,pyqtSignal
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import sys  
import os
from random import randint
import json
import serial
import time
import numpy as np
from PyQt5.QtCore import QThread
global pressure_pdata
global fio2_pdata
global lpressure
import threading
import RPi.GPIO as GPIO
global ini,kz,ex_time
ex_time = 1.5
ini = 0
kz = 0
global rap,data_line
rap = 0
GPIO.setmode(GPIO.BCM)
import Adafruit_ADS1x15
#from pyky040 import pyky040
import sys

global gf,ti,sangi
ti = 0
sangi = 0
global plan,lavs,ie_value
ie_value = 2
lavs = 0
global rr_value,i_rr,test_ex
test_ex = 4
i_rr = 0
rr_value= 0
plan = 0
sys.setrecursionlimit(10**3)
global adc
adc = Adafruit_ADS1x15.ADS1115(address=0x48)
global pressure_support
global pressure_val,volume_val,fio_val,peep_val
global in_time,out_time
global graph,ps_change
global mod_val,mod_val_data,value
global emergency
emergency = 0
value = 0
mod_val_data = 0
mod_val = 1
ps_change = 0
global data_m,control,ti_value
global trigger_data,ps_control
trigger_data = -3
global currentPo,Slide
Slide = 0
currentPo = 0
global read_ser,pressured,pressurel,pressures 
read_ser = []
pressured = []
pressurel = []
pressures = []
global p_s,flag,p_value,p_list,p_cal
p_cal = []
p_list = []
p_s = []
flag = 0
p_value = 0
GAIN = 1


class breathWorker(QThread):
    
#    sigDataupdate = Signal(dict)
    stopSignal = pyqtSignal()
    running = False
    breathStatus = 0
    currentPressure = 0
    pressureCycleValue = 0
    global graph

    def __init__(self):
        super().__init__()
    #    print("setup pwm ")
        

        # self._key_lock = threading.Lock()
        self._exhale_event = threading.Event()
        self._inhale_event = threading.Event()

        GPIO.setup(12, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        
        GPIO.setup(14, GPIO.OUT)
        GPIO.setup(19, GPIO.OUT)
        GPIO.setup(26, GPIO.OUT)
        GPIO.output(14,GPIO.HIGH)
        GPIO.output(19,GPIO.HIGH)
        self.o2PWM = GPIO.PWM(12, 50)
        self.pPWM = GPIO.PWM(13, 50)
###
        
    def update_pwm_Data(self):
        global pressure_val,volume_val,fio_val,mod_val
        global in_time,out_time,ie_value

        
        
        
        global bpm_val
  #      ie_pdata =2
        bpm = bpm_val
        ie_pdata = int(ie_value)
#        print('bpm_val',bpm_val)
        breathCount = 60 / int(bpm)
#        print('breathcount',breathCount)
    
        inhaleTime = (breathCount/(ie_pdata+1)) 
        exhaleTime = (breathCount ) - inhaleTime

#        print('ie',ie_pdata)        
        in_time = inhaleTime
        out_time = exhaleTime
#        print('in',inhaleTime)
#        print('out',exhaleTime)
        
        
#        self.fetch_data()
        
        
        ###
        '''
        pressure_pdata= int(lpressure.text())
        global fio2_data
        fio2_data= int(lfio2.text())
        global volume_pdata
        volume_pdata = int(lvol.text())
        print('p_data',pressure_pdata)
        print('f_data',fio2_data)
        print('v_data',volume_pdata)
        '''
        ###
        pressure_pdata = int(pressure_val)
#        print('p_data',pressure_pdata)
        volume_pdata = int(volume_val)
#        print('v_data',volume_val)
        fio2_data = int(fio_val)   
#        print('f_data',fio2_data)
        
  #      print('pressure_pdata',pressure_pdata)

        
        
        #self._key_lock.acquire()
        #self.o2DC = pressure_pdata
        #self.pDC = fio2_data
        pressPercent = 0
        oxyPercent = 0
        if(fio2_data)>21 and fio2_data > 50:
            oxy_value = float(fio2_data)/100
            pressPercent = float(volume_pdata) * (1-oxy_value)
            oxyPercent = float(volume_pdata) * oxy_value
        elif(fio2_data)>21 and fio2_data < 51:
            oxy_value = float(fio2_data)/100
            pressPercent = float(volume_pdata) * oxy_value
            oxyPercent = float(volume_pdata) * (1-oxy_value)
        else:
            pressPercent = volume_pdata
            oxyPercent = 0
            
#        print("Percents: ", pressPercent,oxyPercent)
        if(mod_val == 1 or mod_val == 5):
            self.pressureCycleValue = self.readPressureValues(pressPercent,oxyPercent)
        if(mod_val in [4,6]):
            pressure_pdata = pressure_pdata*50
            self.pressureCycleValue = self.readPressureValues(pressure_pdata,oxyPercent)
        if(mod_val in [2,3])  :
#            pressure_pdata = pressure_pdata*30
            self.pressureCycleValue = self.readvolumeValues(pressure_pdata,oxyPercent)
##            print('pre30',pressure_pdata)
        if(mod_val == 5):
            pressure_pdata = pressure_pdata*30
            self.pressureCycleValue = self.readPressureValues(pressure_pdata,oxyPercent)
            
            
#        print("pressureCycleValue")
#        print(self.pressureCycleValue)
        self.intime = in_time
        self.outtime = out_time
        self.in_t = self.intime # 0.3 
        self.out_t =  self.outtime # 0.3 
#        print('in-time',in_time)
#        print('out-time',out_time)
#        print("In and out" + str(self.in_t) + str(self.out_t))
   #     self.peep = self.lpeep.text()
  
        

    def stop(self):
        print("stopping breather thread")
        self.pPWM.ChangeDutyCycle(0)
        self.o2PWM.ChangeDutyCycle(0)
        print('duty_cycle_off')
        
        
        
        GPIO.output(14,GPIO.HIGH)
        GPIO.output(26,GPIO.HIGH)
 #       self.o2PWM.stop()
 #       time.sleep(1)
#        self.pPWM.stop()
        self.running = False

    def run(self):
        
        global graph,mod_val_data,control,value,ti_value,ti,two,lamda_b,test
        global ti_val,pressure_support,ps_control,es,sangi,currentP,currentPo
        global mod_val,plan,ps_change,ex_time,lavs,peep_val,test_ex
        GPIO.output(14,GPIO.LOW)
        self.o2PWM.start(0)
        self.pPWM.start(0)
        
#        print("starting breather thread"+ str(self.o2DC)+str(self.pDC)+str(self.in_t)+str(self.out_t)+str(self.peep))
        QThread.msleep(1)
        
                


        if (mod_val == 4):
             
             print('in mode4')
 #            plan = 0
 #            graph = 1
 #            control = 1

             while self.running:
                 end = time.time()+15
                 plan = 0
                 a = 1   
                 while(time.time()<end):
              #       drk_lav = time.time()
                     if (mod_val_data == 1):
                             

                            graph = 0

                            control = 0
                            one = time.time()

                            while(test <= pressure_val):
                                self.pwm_ps_in()
      
                            two = time.time()-one
                            
                            time.sleep(1)
                            print('sleep')


                            graph = 1
                            print('is it')
                            
                            while(test >= es):
                                self.pwm_ps_no()
                            #    drk = 1

                            print('pwm_ps_no')
                            if(test < es or test < 8):
                                
                                drk = 0#ti_value/4):

                            mod_val_data =0
                            plan = 1
                            a = 1
                            print('end')
                            try:
                                ex_time = lamda_b-lamda
                                print('ex_time',lamda_b-lamda)
                            except:
                                drk = 0
                            sangi = 1
                     else:
                         graph = 1
                         control = 1
                         if(a == 1):
                             lamda = time.time()
                         
                         self.pwm_ps_out()
                         a = 0

                         
                 if(plan ==0 and mod_val_data == 0):
                      print('mode changed to 1')
                      mod_val = 3
                      break
        
        if ( mod_val == 3):
            print('mode3')
            while self.running:
                
                self.pwm_in()
                time.sleep(0.1)
                self.pwm_out()
                if (lavs == 1 and mod_val_data == 1):
                    print('in round 2')
                    mod_val = 4
                    mod_val_data = 1
                    lavs = 0
                    self.run()
                    
                                        
           
        if (mod_val == 1 ):
            print('mode 1/2 enabled')
            while self.running:
                
                self.pwm_in()
                time.sleep(0.1)
                graph == 1
          #      print('mode 1')
                self.pwm_out()

                    

                    
        if ( mod_val == 2):
            while self.running:
                
                self.pwm_in()
                time.sleep(0.1)
                self.pwm_out()


                    

        if (mod_val == 5):
            print('mode 5 enabled')
            while self.running:
                print('mode 5')
                self.pwm_in()
            while(self.running == False):
                    print('mode 5 off')
                    self.pwm_out()
                    break
        
               
   

    def pwm_in(self):


                global graph,i_rr,ti
                
                print("self.running.loop")
                print('')
                self.start_time = time.time()
           #     print('start',self.start_time)
                graph = 0
                
                self.pPWM.ChangeDutyCycle(self.pressureCycleValue[0])
                self.o2PWM.ChangeDutyCycle(self.pressureCycleValue[1])
                
                GPIO.output(26,GPIO.LOW)
                GPIO.output(14,GPIO.LOW)

                self.breathStatus = 0
                i_rr += 1

                
                             
                self._inhale_event.wait(timeout=self.in_t)
#                print('wait')
                self.end = time.time()
                #time.sleep(0.1)
                if(mod_val == 1 or mod_val == 2 or mod_val == 3):
                    ti = ((self.end) - (self.start_time))
                    ti = round(ti,1)
                self.pPWM.ChangeDutyCycle(self.pressureCycleValue[0]/2)
                self.o2PWM.ChangeDutyCycle(self.pressureCycleValue[1]/2)    
   #             print('ti',ti)    
    def pwm_out(self):
                
                global graph,peep_val,ti,currentPo
                global rr_value,test,test_ex
                self.peep = int(peep_val)
                
           #     print('peep',peep_val)
           #     print(self.peep)
           #     print("pwm_out")
                
                graph = 1
                self.p_out_start_time = time.time()
                ###
                '''
                if peep_val in [4,5,6]:
                    self.peep = 30
                if peep_val in [7,8,9]:
                    self.peep = 20
                if peep_val in [10,11,12]:
                    self.peep = 30
                '''
                ###
                self.o2PWM.ChangeDutyCycle(self.peep)
                self.pPWM.ChangeDutyCycle(self.peep)
          #      print('peep',self.peep)
                GPIO.output(26,GPIO.HIGH)
#                peep_var = peep_val+2
      #          print('test: peep:',test,peep_val)
                
                if(test_ex<= peep_val and currentPo == 1):
#                    GPIO.output(14,GPIO.HIGH)
#                    print('test: peep_var',test_ex,peep_val)
#                    print('peep achieved:',currentPo)
#                    time.sleep(1)
#                    GPIO.output(14,GPIO.LOW)
                    currentPo = 0

                self.breathStatus = 1
                GPIO.output(14,GPIO.HIGH)
                self._exhale_event.wait(timeout=self.out_t)
                self.p_out_end_time = time.time()
                exhale_time = self.p_out_end_time - self.p_out_start_time
                print('Exhale_time',exhale_time)
                self.end_time = time.time()
           #     print('end_time',self.end_time)
                if(mod_val == 1 or mod_val == 2 or mod_val ==3):
           #         ti = (int(self.end_time) - int(self.start_time))
                     rr_value = int(60/(int(self.end_time) - int(self.start_time)))

    def pwm_ps_out(self):
                global graph,peep_val,ti
                global rr_value           
                graph = 1
                self.start_time = time.time()
                self.o2PWM.ChangeDutyCycle(1)
                self.pPWM.ChangeDutyCycle(1)
                GPIO.output(14,GPIO.HIGH)
                GPIO.output(26,GPIO.LOW)
                self.breathStatus = 1
 #               self.o2PWM.start(0)
#                self.pPWM.start(0)
    
    def pwm_ps_in(self):

                global graph,i_rr,mod_val_data,ti

                self.pPWM.ChangeDutyCycle(self.pressureCycleValue[0])
                self.o2PWM.ChangeDutyCycle(self.pressureCycleValue[1])
                
                GPIO.output(26,GPIO.HIGH)
                GPIO.output(14,GPIO.LOW)
                self.breathStatus = 0
                i_rr += 1
                
    def pwm_ps_no(self):
                global graph,peep_val,ti,Slide
                global rr_value
                self.peep = peep_val
                zero = self.pressureCycleValue[0]/2
                one = self.pressureCycleValue[1]/2
#                print('zero',zero)
#                print('one',one)
                graph = 1
                Slide = 1
                self.o2PWM.ChangeDutyCycle(zero)
                self.pPWM.ChangeDutyCycle(one)
                self.breathStatus = 1

    def readPressureValues(self, pressValue, oxValue):
        pressValuFromJson = 0
        oxyValuFromJson = 0
        with open('pressure.json') as data_file:
            data = json.load(data_file)
            for restaurant in data['PressureValues']:
                minSatisfied = int(restaurant['PressureValue']['min'])<=int(pressValue)
                maxSatisfied = int(restaurant['PressureValue']['max'])>=int(pressValue)
                if(minSatisfied and maxSatisfied):
              #      print("pressVal",restaurant['PressureValue']['value'])
                    pressValuFromJson = restaurant['PressureValue']['value']
            for oxyValue in data['OxygenValues']:
                minSatisfied = int(oxyValue['OxygenValue']['min'])<=int(oxValue)
                maxSatisfied = int(oxyValue['OxygenValue']['max'])>=int(oxValue)
                if(minSatisfied and maxSatisfied):
          #         print("Oxygen",oxyValue['OxygenValue']['value'])
                    oxyValuFromJson = oxyValue['OxygenValue']['value']

            return pressValuFromJson,oxyValuFromJson
    def readvolumeValues(self, pressValue, oxValue):
        pressValuFromJson = 0
        oxyValuFromJson = 0
        with open('volume.json') as data_file:
            data = json.load(data_file)
            for restaurant in data['VolumeValues']:
                minSatisfied = int(restaurant['VolumeValue']['min'])<=int(pressValue)
                maxSatisfied = int(restaurant['VolumeValue']['max'])>=int(pressValue)
                if(minSatisfied and maxSatisfied):
#                    print("VolumeValues satisy")#,restaurant['VolumeValue']['value'])
                    pressValuFromJson = restaurant['VolumeValue']['value']


            return pressValuFromJson,oxyValuFromJson        
        

class backendWorker(QThread):
    threadSignal = pyqtSignal(dict)
    stopSignal =  pyqtSignal()
    dataUpdate = None
    firstLaunch = True
    currentVolData = 0
    global gf

    
    def __init__(self, startParm):
        super().__init__()
        #self.running = True
        self.startParm = startParm   # Initialize the parameters passed to the task
        print('startParm')
        self.dataDict = {
            "curr_act" : 0,
            "o2conc" : [],
            "AirV" : [],
            "Dpress+" : [],
            "Dpress-" : [],
            "press+" : [],
            "press-" : [],
            "co2" : [],
            "temp" : [],
            "hum" : []
        }
        self.seam = []
        self.currentPressure_list = []
        #GPIO.setup(4, GPIO.OUT)

    def stop(self):
        global emergency
        emergency = 0
        print("stopping thread")
        self.running = False
        
        
    def initSerData(self):
        
        print('init_ser')
        
        ###
        '''
            
            self.ser = serial.Serial("/dev/ttyUSB1",9600)  #change ACM number as found from ls /dev/tty/ACM*
            #self.ser1 = serial.Serial("/dev/ttyUSB1",9600)
            self.ser.baudrate=9600
            #self.ser1.baudrate=9600
        '''
        ###
        
    def sendValues(self):
        #GPIO.output(4,GPIO.HIGH)
        #time.sleep(0.2)
        #GPIO.output(pin,GPIO.LOW)
        data2transfer = self.dataUpdate["pressure"]+','+self.dataUpdate["intime"]+','+self.dataUpdate["outtime"]+','+self.dataUpdate["peep"]+','+self.dataUpdate["fio2"]
        print("DEBUG: "+data2transfer)
        #self.ser1.write(data2transfer.encode())

    def getdata(self):
        global gf,control,lamda_b,lavs,in_time,ex_time
        global ini,rap,adc,ti_val,ti_value,test
        global pressure_support,pressure_val
        global firstvalue,trigger_data,sangi,Slide
        global graph,mod_val_data,currentP,currentPo
        global ps_change,kz,value,peep_val,test_ex
        global emergency,p_s,flag,p_value,p_list,p_cal
        global fio_val
         
        ko = 0
        
        

        read_ser = []
        presstemp = []
        pressurel = []
        
        slide_p = int(pressure_val+peep_val)
        slide_peep = int(pressure_val)/4

        data = [0]*4

#        try:
        
        for i in range(3):
            data[i] = adc.read_adc(i, gain=GAIN)
            sen_data = 1
        time.sleep(0.5)
#        except:
        print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*data))
#            sen_data = 0
        
        if(sen_data ==1):    
            p_data = (data[0]/8000) #*0.1875)/1503
            
            p_data = round(p_data,1)
            p_list.append(p_data)
 #           print('sensor_data_list',p_list)
        #if(mod_val in [2]):    
        if(graph == 0) and (sen_data == 1):   
            p_data = round(p_data,1)
#            print('sensor_data',p_list)
            print('len',len(p_s))
            print('p_s',p_s)
            p_s.append(p_data)
            present_value = p_s[-1]
            if(present_value<3 and present_value>2.5):
                if(present_value >0):  
                    p_value = present_value
            if(present_value>3):
                try:
                    temp1 = present_value
                    temp2 = p_s[-2]
                    temp3 = p_s[-3]
                    temp4 = p_s[-4]
                    temp5 = p_s[-5]
                    temp6 = p_s[-6]
                    temp7 = p_s[-7]
                    temp8 = p_s[-8]
                    temp9 = p_s[-9]
                    #temp10 = p_s[-10]
                    #temp11 = p_s[-11]
                    if(temp1 and temp2 and temp3 and temp4 and temp5 and temp6 and temp7 and temp8 and temp9 )>3:
                        p_value = present_value
                except:
                    n = 0
            p_cal.append(p_value)
 #       print('calulated_sensor_value',p_cal)
        pressurel.append(p_value)       
#        print('8888',pressurel)  
        #else:
            #pressurel.append(p_data)

  
        if(graph == 0):
#            print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*data))

#            print(data[0]/8000)
            diff_pre = float(data[1]*0.1875)

            try:
                self.dataDict["Dpress+"].clear()
                self.currentPressure_list.clear()

            except:
                drk = 1

            
            if(ini == 0):
                    firstvalue = round(pressurel[0],2)
                    currentPressure = firstvalue
                    ini += 1

            else:
                    nextvalue = round(pressurel[-1],2)

                    if(nextvalue > firstvalue):
                        currentPressure = nextvalue
                        firstvalue = currentPressure
                    elif(nextvalue < firstvalue):
                        currentPressure = firstvalue
                        firstvalue = currentPressure
                    else:
                        currentPressure = firstvalue
            
            if (currentPressure < pressurel[0]):
                currentPressure = pressurel[0]
            else:
               currentPressure = firstvalue

            if(len(self.dataDict["Dpress+"])>300):
                self.dataDict.clear()
                self.dataDict = {
                                    "curr_act" : 0,
                                    "o2conc" : [],
                                    "AirV" : [],
                                    "Dpress+" : [],
                                    "Dpress-" : [],
                                    "press+" : [],
                                    "press-" : [],
                                    "co2" : [],
                                    "temp" : [],
                                    "hum" : []
                                    }
            press = round(currentPressure,2)

            pressure = ((press-2.5)/0.2)


            pressure = (round(pressure,1))
            test = pressure*5
            test_in = pressure*5
            ###
            '''
            if mod_val==2 and volume_val < test_in:
                emergency = 3
            '''
            ###   volume based pressure value
        
            if mod_val in [3,4]:
                pressure_va = pressure_val + peep_val
                
                if(pressure_val < test_in):
                    emergency = 3

                if(pressure_va < test_in):
                    test_in = ressure_va
                    self.dataDict["Dpress+"].append(test_in) #check its wrong

                else:
                    self.dataDict["Dpress+"].append(pressure*5) #check its wrong
                    
             
            else:
                    self.dataDict["Dpress+"].append(test_in)

        if (graph == 1):
            
            
            diff_pre = float(data[1]*0.1875)/8000

            self.currentPressure_list.append((data[0])/8000)
 #           print((data[0])/8000)
            p = self.currentPressure_list[-1]
            death =self.currentPressure_list[:10]

            
            if len(death) >= 4:
                naoh = sum(death)/len(death)
                
                naoh = round(naoh,1)
                
            if mod_val in [1,2,3,5] and len(death) >= 4 and len(death) < 15:
                if(naoh <= 2.6):

                    emergency = 1
                else:
                    emergency = 0

            pi = p
            pu = ((pi-2.5)/0.2)
            pu = (round(pu,1))
            currentP = pu*5
            test_ex= pu*5

                 
            peep_var = peep_val+2

                
            if(mod_val == 4 or mod_val == 3):
               
                if(mod_val == 4):
                    time.sleep(0.5)
                else:
                    time.sleep(0.2)
                if(sangi == 1):
                    print('waiting for exhalation')
                    time.sleep(1.5)

                trigger_data = abs(trigger_data)
                trigger = peep_val - trigger_data
                sangi = 0
                self.false_trigger = len(self.currentPressure_list)

                if (control == 1 and currentP < trigger and self.false_trigger > 10):# trigger_data):
                    lamda_b = time.time()
                    
                    mod_val_data = 1
                    lavs = 1
                    print('set_pre,act_pre: ',trigger,currentP)

            
            if(len(self.dataDict["Dpress+"])>300):
                self.dataDict["Dpress+"].clear()
                gf = 1
                self.dataDict = {
                        "curr_act" : 0,
                        "o2conc" : [],
                        "AirV" : [],
                        "Dpress+" : [],
                        "Dpress-" : [],
                        "press+" : [],
                        "press-" : [],
                        "co2" : [],
                        "temp" : [],
                        "hum" : []
                    }
            

            if (Slide == 1):
                
                for i in np.arange(slide_p,slide_peep,-0.5):
                    roundi = round(i,1)
                    self.dataDict["Dpress+"].append(roundi)
                    Slide = 0
                    
            test = pu*5

            if test > peep_val:
                testu = test
            else:

                testu = test#peep_va
   
            self.seam.append(testu)
            self.s = self.seam[-1]
          
            if (self.s < peep_var):
                currentPo = 1


            self.dataDict["Dpress+"].append(self.s)
            ini = 0

   #inc in oxygen %

       
        return self.dataDict


    def run(self):
        global data_m
        # Do something...
        if self.firstLaunch :
            self.initSerData()
            self.firstLaunch=False
        #self.sendValues()
        print("starting thread")
        while self.running:
            data_m = self.getdata()
        #    print('data_m',data_m)
   #         if data_m != None:
   #             self.threadSignal.emit(data_m)

#             QThread.msleep(10)
        #GPIO.output(4,GPIO.LOW)
        print("stopped thread")
        print('bworker',data_m)
        #self.threadSignal.emit(self.startParm)



class App(QFrame):

    def __init__(self):
        super().__init__()
        self.title = 'ventilator'
        self.pmean = []
        self.mean = []
        self.mean_v = 0
        
        self.left = 10
        self.top = 10
        self.width = 200
        self.height = 100
        self.on = 0
        
        self.initUI()
        self.ie_value = 2
      
        self.setStyleSheet("background-color: black;")
        
        self.bthThread = breathWorker()
        self.bthThread.stopSignal.connect(self.bthThread.stop)
        
        self.beThread = backendWorker('hello')

        self.beThread.stopSignal.connect(self.beThread.stop)
        self.update_parameters()
        self.graph()
#        self.encoder()

        
        
        

        
    def fetch_data(self):
        
        ## computing breathing intervals ##
        global in_time,out_time,bpm_val

        bpm = bpm_val
        print('bpm_val',bpm_val)
        ie_pdata = int(self.ie_value)

        ###
        '''
        
        if self.lie.text() == '0:0':      
            ie_pdata = 2
        if self.lie.text() == '1.1':      
            ie_pdata = 3
        if self.lie.text() == '1.2':      
            ie_pdata = 4
        if self.lie.text() == '1.3':      
            ie_pdata = 5
        if self.lie.text() == '1.4':      
            ie_pdata = 6
 #       print('ie',ie_pdata)   
# # # # # # # # # #         print('ie'+str(ie_pdata))
        ###
        '''
        ###
        self.breathCount = 60 / int(bpm)
        print('breathcount',self.breathCount)
    
        self.inhaleTime = (self.breathCount/(ie_pdata+1)) 
        self.exhaleTime = (self.breathCount ) - self.inhaleTime
        
#        print('ie',ie_pdata)        
        in_time = self.inhaleTime
        out_time = self.exhaleTime
#        print('in',self.inhaleTime)
#        print('out',self.exhaleTime)
        
            #self._key_lock.release()    

    def update_parameters(self):
        self.pressure_value = False 
        self.volume_value = False
        self.bpm_value = False
        self.fio2_value = False
        self.peep_value = False   
        
    def graph(self):
        global rap
        global gf
        pg.setConfigOptions(antialias=True)
        self.graphwidget = pg.PlotWidget()
        self.graphwidget.setYRange(0,50)
        #self.x = list(range(100))  # 100 time points
        self.y = [randint(0,0) for _ in range(300)]  # 100 data points
        
        
        self.graphwidget.setBackground('#0000')
        self.graphwidget.setLabel('left', 'Pressure')
        self.graphwidget.setLabel('bottom', '*100 (Time in milliseconds) ')
        #self.graphwidget.getPlotItem().hideAxis('bottom')

        pen = pg.mkPen(color='y')
        self.data_line =  self.graphwidget.plot(self.y, pen=pen) #fillLevel=0,brush=(150,50,150,50))           #pen=pen)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100 )
        self.timer.timeout.connect(self.update_plot_data)
#        try:
#            print('yes yes')
#            self.timer.timeout.connect(self.bthThread.update_pwm_Data())
#        except:
#            drk = 0
#            print('no0')
        self.timer.start()
        self.layout.addWidget(self.graphwidget,2,0,5,4)
        #self.data_line.clear()
        

    def update_plot_data(self):
        
        global data_m,rr_value,i_rr,ti,mod_val,pressure_val,pressure_pdata,two,ex_time
        global emergency    
        a = 0
        if emergency != 0:
            if emergency == 4:
                self.alarm.setText('High-oxy')
                self.alarm.setStyleSheet("color: white;  background-color: red")

            if emergency == 1:
                self.alarm.setText('dis-connect')
                self.alarm.setStyleSheet("color: white;  background-color: red")
            if emergency == 3:
                self.alarm.setText('High-Pr')
                self.alarm.setStyleSheet("color: white;  background-color: red")
            if emergency == 2:
                self.alarm.setText('High-vol')
                self.alarm.setStyleSheet("color: white;  background-color: red")

        else:
            self.alarm.setText('-')
            self.alarm.setStyleSheet("color: white;  background-color: black")            
            
        
        if self.bthThread.breathStatus == 0:
            global data_m
            #print('datarec', data_m)
            #self.data_get()
            try:
                if mod_val != 5:
                    self.bstop.setEnabled(False)
            except:
                drk = 1
            self.lbcadata.setText('Inhale')
            #press = self.lpresd.text()
            #self.lpresd.setText(press)
            if(mod_val == 4):
                try:
                    ti = round(two,1)
                    self.lbtidata.setText(str(ti))
      
                except:
                    drk = 0
            else:
                self.lbtidata.setText(str(ti))
                
            #self.lpbdata.setText(press)
            if (self.on == 1):
            
                vol = self.lvol.text()
                vv = int(vol)
#                self.lmvd.setText(str(vv))
                volc = int(vol)
#                self.lbvedata.setText(str(volc))
                if (mod_val == 4 or mod_val == 2 or mod_val == 3):
                    
                    self.lmvd.setText(str(pressure_val*30))
                    self.lbvedata.setText(str(pressure_val*30))
            #        print('mode 2,4')
                elif (mod_val == 5):
                    self.lbvedata.setText('1400')
                    self.lmvd.setText('1400')
                    
                else:
                    self.lbvedata.setText(str(volc))
                    self.lmvd.setText(str(vv))
                   # print('no change')
                    
         #   peep = int(self.lpeep.text()) + randint(0,10)
            self.lbpeepdata.setText('-')

            try:
                
                self.pip = max(data_m['Dpress+'])
                pressure = data_m['Dpress+'][-1]
 #               print(pressure)
                self.lpresd.setText(str(pressure))
                
#                if mod_val in [2,3,4]:
                    
                
                
#                    print('in  2')
#                   if(pressure > pressure_val):
#                       self.lpresd.setText(str(pressure_val))
                   #     print('prd',pressure_val)
     #            #       print('prrrd',pressure)
#                    else:
#                     self.lpresd.setText(str(pressure))
                 #       print('press',pressure)
                    
                if(mod_val == 1 or mod_val ==5):
                    self.lpresd.setText(str(pressure))
                
                
                
                
          #      self.mean.append(self.pip)
          #      self.pmean = self.mean[-4:]
           #     print('pmean',self.pmean)
           #     print('len',len(self.pmean))
           ###
                '''
                if (len(self.pmean)%4) == 0:
                    self.mean = self.pmean[-4:]
                    self.mean_v = sum(self.mean)/4
             #       print('mean',self.mean_v)
                    if(i_rr < 3):
                        print('i-rr',i_rr)
                        self.lbpmeandata.setText(str(self.mean_v))
                        '''
           ###

                
                if(mod_val == 2 or mod_val == 4 or mod_val == 3):
          #         self.pip = pressure_val
                    a = max(data_m['Dpress+'])
                    
 #                   print('a',a)
                    self.pip = a 
                    if(mod_val == 2 or mod_val == 3):
                        self.lbpdata.setText(str(self.pip))
                    if mod_val in [4]:
                        self.lbpdata.setText(str(self.pip))
                        self.mean = float((self.pip * ti) + (float(self.peep) * ex_time))
                        self.pmean = self.mean/(ti+ex_time)
                        self.pmean = "{:.1f}".format(self.pmean)
                        self.lbpmeandata.setText(str(self.pmean))
                        time = int(ex_time-ti)
                #        print('time',time)
                        rr_value = 60 /(time)
                        rr_value = round(rr_value,1)
              #          print('rr',rr_value)
                        self.lrrd.setText(str(rr_value))
                #        print('pip',self.pip)
               #         print('peep',self.peep)
               #         print('ti',ti)
                     #   print('exti',ex_time)
                    if(mod_val == 5):
                        self.lbpmeandata.setText('-')
                        
                        
                else:
                    self.lbpdata.setText(str(self.pip))
                

                    
            except:
                self.lbpdata.setText('0')
                
  
        #print('pip',self.pip)   
        if self.bthThread.breathStatus == 1:

                
            self.bstop.setEnabled(True)
            self.bthThread.update_pwm_Data()
            self.lbcadata.setText('Exhale')
            #print('datarec', data_m)
            self.lpresd.setText('0')
            self.lbtidata.setText('-')
            self.lbpdata.setText('-')
            #self.lpbdata.setText(press)
            if(self.on == 1):
#                 vol = self.lvol.text()
        #        vv = int(vol)+int(randint(-10,15))
                self.lmvd.setText('-')
          #      volc = int(vol)+int(randint(-10,5))
                self.lbvedata.setText('-')

      #      print('pip',self.pip)
      #      print('inhale',self.inhaleTime)
      #      print('peep',self.peep)
      #      print('exhale',self.exhaleTime)
            
            try:
                self.peep_d = (data_m['Dpress+'][-1])
     #           print('peep',self.peep_d)
#                if( self.peep_d < 2.7):
                self.peep = round(self.peep_d,1)

        #        print('pmeen',pmeen)
          #      peep = (self.lpeep.setText(str(pmeen)))
                self.lbpeepdata.setText(str(self.peep))
                self.lrrd.setText(str(rr_value))
                self.mean = float((self.pip * self.inhaleTime) + (float(self.peep) * self.exhaleTime))
      #          print('mean',self.mean)
                if(ti != 0):
                    if(mod_val == 4):
                        self.lbpmeandata.setText('-')
                        self.lbpdata.setText('-')
                        
                        
                    else:    
                        ti = float(ti)
                        total = self.inhaleTime + self.exhaleTime
                 #       print('total',total)
                        self.pmean  = self.mean / total
        #                print('pmean',self.pmean)
       #                 print('ti',ti)
       #                 self.pmean = "{:.1f}".format(self.pmean)
            #            self.lbtidata.setText(str(ti))
                        self.pmean = "{:.1f}".format(self.pmean)
                        self.lbpmeandata.setText(str(self.pmean))
                               #             print('pmean',self.pmean)
            except:
                drk = 0
            

            
        
        try:
                #self.y = self.y[1:]
                #self.y.append(int(data_m['Dpress+'][-1]))                pressure = data_m['Dpress+'][-1]
#                pres = round()
#                print('pressure',pressure)
                #*5
                
              #  o2s = str(data_m["o2conc"][-1])
                o2 = int(data_m["o2conc"][-1]) #"{.:2f}".format(o2s)
      #          print('o2', o2)
                o2s = "{:.1f}".format(o2)
                if(o2 > 100):
                    self.laprd.setStyleSheet("background-color: red")
                    self.laprd.setText(str(o2s))
                if(o2 < 100):
                    self.laprd.setStyleSheet("background-color: green")
                    self.laprd.setText(str(o2s))
                ###
                '''    
                if mod_val in [2,3,4]:
                   # print('in  2')
                    if(pressure > pressure_val):
                        self.lpresd.setText(str(pressure_val))
                   #     print('prd',pressure_val)
                 #       print('prrrd',pressure)
                    else:
                        self.lpresd.setText(str(pressure))
                 #       print('press',pressure)
                    
                if(mod_val == 1 or mod_val ==5):
                    self.lpresd.setText(str(pressure))
                    
                
                #print('try',data_m['Dpress+'][-1])
                #print('y',self.y)
       #         print('plvvv',pressure)
               # self.data_line.setData(self.y)
               '''
               ### 
                

        except:
            drk = 1
            
            
        try:
            
                self.y = self.y[1:]
                #v = int(data_m['Dpress+'][-1])
                self.y.append(int(data_m['Dpress+'][-1]))
                self.data_line.setData(self.y)
                ##for i in range(6):
                  #  self.data_line.setData(self.y[i], pen=(i,3))
          #      print('Graph plotting')
        except:
              g = 1
        #      print('Graph error')
            
         #   print('NO sensor data recevied')

        #print('graph_plot')
         
        #if(rap == 1):
           # self.data_line.clear()
           # print('graph_clear')
       # Update the data.
        
            
        
    def graph2(self):
        self.graphWidget = pg.PlotWidget()
        self.x2 = list(range(100))  # 100 time points
        self.y2 = [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('#0000')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line2 =  self.graphWidget.plot(self.x2, self.y2, pen=pen)
        self.timer1 = QtCore.QTimer()
        self.timer1.setInterval(100)
        self.timer1.timeout.connect(self.update_plot_data2)
        self.timer1.start()
        self.layout.addWidget(self.graphWidget,3,0,3,4)

    def update_plot_data2(self):

        self.x2 = self.x2[1:]  # Remove the first y element.
        self.x2.append(self.x2[-1] + 1)  # Add a new value 1 higher than the last.

        self.y2 = self.y2[1:]  # Remove the first 
        self.y2.append( randint(0,100))  # Add a new random value.

        self.data_line2.setData(self.x2, self.y2)  # Update the data.

    def graph3(self):
        self.graphWidget = pg.PlotWidget()
        self.x = list(range(100))  # 100 time points
        self.y = [randint(0,100) for _ in range(100)]  # 100 data points

        self.graphWidget.setBackground('w')

        pen = pg.mkPen(color=(255, 0, 0))
        self.data_line =  self.graphWidget.plot(self.x, self.y, pen=pen)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data3)
        self.timer.start()
        self.layout.addWidget(self.graphWidget,6,0,3,3)

    def update_plot_data3(self):

        self.x = self.x[1:]  # Remove the first y element.
        self.x.append(self.x[-1] + 1)  # Add a new value 1 higher than the last.

        self.y = self.y[1:]  # Remove the first 
        self.y.append( randint(0,100))  # Add a new random value.

        self.data_line.setData(self.x, self.y)  # Update the data.
    
     

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.readSettings(0)
        self.createGridLayout()
        self.bes.hide()
        self.BEs.setVisible(False)
        
        windowLayout = QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)

        self.setLayout(windowLayout)
        self.mode_set = 2
        
        self.show()
    def readSettings(self,i):
        global mod_val
        params = ["pressure", "volume", "bpm", "peep", "fio2"]
        # reading the data from the file
        
        if(i == 0):
        
            with open('settings.txt') as f:
                data = f.read()
           #     print('default')
        
        if(i == 1):
               with open('mode1.txt') as f:
                data = f.read()
              #  print('default')
        if(i == 2):
               with open('mode2.txt') as f:
                data = f.read()      
        if(i == 3):
               with open('mode3.txt') as f:
                data = f.read()       
              
                
    #    print("Data type before reconstruction : ", type(data))

        # reconstructing the data as a dictionary
        self.settings = json.loads(data)

        #self.settings = {}
        print("Data type after reconstruction : ", type(self.settings))
        for param in params:
            try:
                self.settings[param]["min"]
                self.settings[param]["max"]
                self.settings[param]["default"]

            except KeyError as e:
                print('KeyError - missing key ["%s"]["%s"]' % (param, str(e)) )
             
    
    def label_reset(self):
        self.lpressure.setText('0')
        self.lvol.setText('0')
        self.lbpm.setText('1')
        self.lpeep.setText('0')
        self.lfio2.setText('0')
        
    def stop_action(self):
        Bstart = QPushButton('Start')          #start button
        Bstart.setFont(QFont('Arial', 15))
        Bstart.setStyleSheet("background-color: white")
        Bstart.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        Bstart.clicked.connect(self.on_process)
        self.layout.addWidget(Bstart,1,6)
        Bstart.clicked.connect(self.stop)

        
        
    def stop(self):
        
        self.bstop = QPushButton('stop')
        self.bstop.setFont(QFont('Arial', 15))
        self.bstop.setStyleSheet("background-color: grey")
        self.bstop.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.bstop,1,6)

        self.bstop.clicked.connect(self.off_process)
        self.bstop.clicked.connect(self.stop_action)

        
    def vc(self):
        global pressure_val
        
        self.label_reset()
        self.readSettings(1)
        
        self.lpressure.setText(str(self.settings["pressure"]["default"]))
        pressure_val = int(self.lpressure.text())
        self.lpresd.setVisible(False)
        self.Bti.setEnabled(False)
        self.lvol.setText(str(self.settings["volume"]["default"]))
        
        self.lbpm.setText(str(self.settings["bpm"]["default"]))
        self.lpeep.setText(str(self.settings["peep"]["default"]))
        self.lfio2.setText(str(self.settings["fio2"]["default"]))    
    def ps(self):
        global pressure_val
        
        self.label_reset()
        self.readSettings(1)
        self.lpressure.setText(str(self.settings["pressure"]["default"]))
        pressure_val = int(self.lpressure.text())
        self.Bti.setEnabled(False)
        self.lbpm.setEnabled(False)
        
        self.lvol.setText(str(self.settings["volume"]["default"]))
        self.lbpm.setText(str(self.settings["bpm"]["default"]))
        self.lpeep.setText(str(self.settings["peep"]["default"]))
        self.lfio2.setText(str(self.settings["fio2"]["default"]))
        
    def hfonc(self):
        self.label_reset()
        self.readSettings(2)
        self.Bti.setEnabled(False)
        self.Bpressure.setEnabled(True)
        self.lpressure.setVisible(True)
        self.lpressure.setText(str(self.settings["pressure"]["default"]))
        self.lvol.setText(str(self.settings["volume"]["default"]))
        self.lbpm.setText(str(self.settings["bpm"]["default"]))
        self.lpeep.setText(str(self.settings["peep"]["default"]))
        self.lfio2.setText(str(self.settings["fio2"]["default"]))
        
    def pc(self):
        self.label_reset()
        self.readSettings(1)
        self.lpresd.setVisible(True)
        self.Bti.setEnabled(False)
        self.Bvol.setEnabled(False)
        self.lvol.setVisible(False)
        self.Bpressure.setEnabled(True)
        self.lpressure.setVisible(True)
        self.lpressure.setText(str(self.settings["pressure"]["default"]))
        self.lvol.setText(str(self.settings["volume"]["default"]))
        self.lbpm.setText(str(self.settings["bpm"]["default"]))
        self.lpeep.setText(str(self.settings["peep"]["default"]))
        self.lfio2.setText(str(self.settings["fio2"]["default"]))
        
    def p_callback(self, i):

        if(self.p_en == True):
            v = self.plabel.text()
            value = int(v) + int(i)
            self.slp.setValue(value)
            
        if(self.b_en == True):
            
            v = self.bpmlabel.text()
            value = int(v) + int(i)
            self.slbpm.setValue(value)
            
        if(self.pe_en == True):
            v = self.peeplabel.text()
            value = int(v) + int(i)
            self.slpeep.setValue(value)
        
        if(self.ti_en == True):
            v = self.ti.text()
            value = int(v) + int(i)
            self.slti.setValue(value)
            
        if(self.f_en == True):
            v = self.fio2label.text()
            value = int(v) + int(i)
            self.slfio2.setValue(value)
         
        if(self.v_en == True):
            v = self.vlabel.text()
            if(i == 1):
                value = int(v) + int(i) + 49
            if(i == -1):
                value = int(v) + int(i) - 49
                
            self.slv.setValue(value)  
        #print('en_v',value)

    def s_callback(self):
        if(self.p_en == True):
            self.pupdate_val.click()
            
        if(self.b_en == True):
            self.bupdate_val.click()
            
        if(self.pe_en == True):
            self.peepupdate_val.click()
        
        if(self.ti_en == True):
            self.tiupdate_val.click()
            
        if(self.f_en == True):
            self.fupdate_val.click()
         
        if(self.v_en == True):
            self.vupdate_val.click() 

    def encoder(self):
        
        self.p_en = False
        self.b_en = False
        self.pe_en = False
        self.ti_en = False
        self.fi_en = False
        self.v_en = False
        self.f_en = False
        self.en = pyky040.Encoder(CLK=17, DT=18, SW=27)
        self.en.setup(scale_min=-1, scale_max=1, step=2, chg_callback=self.p_callback, sw_callback = self.s_callback)
        #t = p_en.watch
        #self.en_thread = multiprocessing.Process(self.p_thread)
        self.en_thread = threading.Thread(target=self.en.watch)
        self.en_thread.start()
    
        
    def pressure_set(self):
        global mod_val
        v = self.lpressure.text()
        self.plabel = QLabel(v, self)
        self.plabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.plabel.setMinimumWidth(80)
        self.plabel.setFont(QFont('Arial', 25))
        self.plabel.setStyleSheet("color: white;  background-color: black")
        
        self.slp = QSlider(Qt.Vertical, self)
        self.slp.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        
#        if(mod_val == 4):
#            self.slp.setRange(0, 32)
#        else:
        self.slp.setRange(0,50)
            
        self.slp.setFocusPolicy(Qt.StrongFocus)
        self.slp.setPageStep(1)
        v = self.lpressure.text()
        #self.lpressure.setText(str(v))
        self.slp.setValue(int(v))
        self.slp.valueChanged.connect(self.pupdateLabel)
        self.slp.setTickPosition(QSlider.TicksBelow)
        self.slp.setTickInterval(5)


        self.layout.addWidget( self.slp,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.plabel,6,6)
        

        self.pupdate_val = QPushButton('P update')
        self.pupdate_val.setFont(QFont('Verdana', 13))  
        self.pupdate_val.setStyleSheet("background-color: orange")
        self.layout.addWidget(self.pupdate_val,7,6)
        self.pupdate_val.clicked.connect(self.update_setp)
        self.p_en = True

        
    def update_setp(self):
        global pressure_val

       # self.update_parameters()
        try:
            self.lpressure.setText(self.pressure_values)
            pressure_val = int(self.lpressure.text())
#            print('p update',pressure_val)
        except:
            v = self.plabel.text()
            self.lpressure.setText(v)
           
        pressure_val = int(self.lpressure.text())
        #print('p update',pressure_val)
        self.p_en = False
        #self.p_en = pyky040.Encoder(CLK=7, DT=8, SW=6)
        #self.en_thread.join()
        self.slp.deleteLater()
        self.plabel.deleteLater()
        self.pupdate_val.deleteLater()
    def pupdateLabel(self, value):      
        self.plabel.setText(str(value))       
        self.pressure_values = self.plabel.text()

    def bpm_set(self):
        
        v = int(self.lbpm.text())
        self.bpmlabel = QLabel(str(v), self)
        self.bpmlabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.bpmlabel.setMinimumWidth(80)
        self.bpmlabel.setFont(QFont('Arial', 25))
        self.bpmlabel.setStyleSheet("color: white;  background-color: black")
        
        self.slbpm = QSlider(Qt.Vertical, self) 
        self.slbpm.setRange(1, 20)
        self.slbpm.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        v = int(self.lbpm.text())
        self.slbpm.setValue(v)
        self.slbpm.setFocusPolicy(Qt.StrongFocus)
        self.slbpm.setPageStep(5)
        self.slbpm.valueChanged.connect(self.bpmupdateLabel)
        self.slbpm.setTickPosition(QSlider.TicksBelow)
        self.slbpm.setTickInterval(5)

        self.bpmlabel = QLabel(str(v), self)
        self.bpmlabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.bpmlabel.setMinimumWidth(80)
        self.bpmlabel.setFont(QFont('Arial', 25))
        self.bpmlabel.setStyleSheet("color: white;  background-color: black")

        self.layout.addWidget( self.slbpm,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.bpmlabel,6,6)
        

        self.bupdate_val = QPushButton('BPM update')
        self.bupdate_val.setFont(QFont('Verdana', 13))  
        self.bupdate_val.setStyleSheet("background-color: orange")
        self.layout.addWidget(self.bupdate_val,7,6)
        self.bupdate_val.clicked.connect(self.update_setbpm)
        self.b_en = True
        
    def update_setbpm(self):
        global bpm_val

        try:
            self.lbpm.setText(self.bpm_v)
            bpm_val = int(self.bpmlabel.text())
            print('update bpm',bpm_val)
        except:    
            bpm_val = self.bpmlabel.text()
            self.lbpm.setText(bpm_val)
        
        self.slbpm.deleteLater()
        self.bpmlabel.deleteLater()
        self.bupdate_val.deleteLater()
        self.b_en = False
        #self.update_parameters()
    
    def bpmupdateLabel(self, value):      
        self.bpmlabel.setText(str(value))
        #self.lbpm.setText(str(value))
        self.bpm_v = str(value)     

    def peep_set(self):
        global peep_val

        v = self.lpeep.text()
        self.peeplabel = QLabel(str(v), self)
        self.peeplabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.peeplabel.setMinimumWidth(80)
        self.peeplabel.setFont(QFont('Arial', 25))
        self.peeplabel.setStyleSheet("color: white;  background-color: black")

        self.slpeep = QSlider(Qt.Vertical, self) 
        self.slpeep.setRange(0, 20)
        self.slpeep.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        peep_val = int(self.lpeep.text())
        self.slpeep.setValue(int(peep_val))
        self.slpeep.setFocusPolicy(Qt.StrongFocus)
        self.slpeep.setPageStep(5)
        self.slpeep.valueChanged.connect(self.peepupdateLabel)
        self.slpeep.setTickPosition(QSlider.TicksBelow)
        self.slpeep.setTickInterval(5)


        a = self.peeplabel.text()
####        print('a',a)
        self.layout.addWidget( self.slpeep,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.peeplabel,6,6)
        
        #self.peeplabel = QLabel('Vol update', self)
        #self.peeplabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
       # self.peeplabel.setMinimumWidth(80)
       # self.peeplabel.setFont(QFont('Arial', 10))
       # self.peeplabel.setStyleSheet("color: white;  background-color: black")
       # self.layout.addWidget(self.peeplabel,7,6)

        self.peepupdate_val = QPushButton('peep update')
        self.peepupdate_val.setFont(QFont('Verdana', 13))  
        self.peepupdate_val.setStyleSheet("background-color: orange")
        self.layout.addWidget(self.peepupdate_val,7,6)
        self.peepupdate_val.clicked.connect(self.update_setpeep)
        self.pe_en = True
        
    def update_setpeep(self):
        global peep_val
        try:
            self.lpeep.setText(self.peep_v)
            peep_val = int(self.peeplabel.text())
            print('update peep',peep_val)
        except:
  #         peep_val = int(self.peeplabel.text())
            self.lpeep.setText(peep_val)
            peep_val = int(self.lpeep.text())
        #print('ui_peep',peep_val)
        self.slpeep.deleteLater()
        self.peeplabel.deleteLater()
        self.peepupdate_val.deleteLater()
        self.pe_en = False
        #self.update_parameters()
    
    def peepupdateLabel(self, value):
        
        self.peeplabel.setText(str(value)) 
        self.peep_v = str(value)
        
    def ti_set(self):

        self.slti = QSlider(Qt.Vertical, self) 
        self.slti.setRange(0, 100)
        self.slti.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        self.slti.setFocusPolicy(Qt.StrongFocus)
        v = self.ti.text()
        self.slti.setValue(int(v))
        self.slti.setPageStep(5)
        self.slti.valueChanged.connect(self.tiupdateLabel)
        self.slti.setTickPosition(QSlider.TicksBelow)
        self.slti.setTickInterval(5)

        self.tilabel = QLabel(v, self)
        self.tilabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.tilabel.setMinimumWidth(80)
        self.tilabel.setFont(QFont('Arial', 25))
        self.tilabel.setStyleSheet("color: white;  background-color: black")

        self.layout.addWidget( self.slti,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.tilabel,6,6)

        self.tiupdate_val = QPushButton('ti update')
        self.tiupdate_val.setFont(QFont('Verdana', 10))  
        self.tiupdate_val.setStyleSheet("background-color: orange")
        self.layout.addWidget(self.tiupdate_val,7,6)
        self.tiupdate_val.clicked.connect(self.update_setti)
        self.ti_en = True
        
    def update_setti(self):
        global ti_val
        try:
            self.ti.setText(self.ti_v)
        except:
            v = self.tilabel.text()
            self.lfio2.setText(v)
        ti_val = self.ti.text()
        self.slti.deleteLater()
        self.tilabel.deleteLater()
        self.tiupdate_val.deleteLater()
        self.ti_en = False
        #self.update_parameters()
    
    def tiupdateLabel(self, value):      
        self.tilabel.setText(str(value))
        #self.lfio2.setText(str(value))
        self.ti_v = str(value)     
        

    def fio2_set(self):
        global fio_val

        self.slfio2 = QSlider(Qt.Vertical, self) 
        self.slfio2.setRange(0, 100)
        self.slfio2.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        self.slfio2.setFocusPolicy(Qt.StrongFocus)
        fio_val = self.lfio2.text()
        self.slfio2.setValue(int(fio_val))
        self.slfio2.setPageStep(5)
        self.slfio2.valueChanged.connect(self.fio2updateLabel)
        self.slfio2.setTickPosition(QSlider.TicksBelow)
        self.slfio2.setTickInterval(5)

        self.fio2label = QLabel(str(fio_val), self)
        self.fio2label.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.fio2label.setMinimumWidth(80)
        self.fio2label.setFont(QFont('Arial', 25))
        self.fio2label.setStyleSheet("color: white;  background-color: black")

        self.layout.addWidget( self.slfio2,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.fio2label,6,6)

        self.fupdate_val = QPushButton('fio2 update')
        self.fupdate_val.setFont(QFont('Verdana', 10))  
        self.fupdate_val.setStyleSheet("background-color: orange")
        self.layout.addWidget(self.fupdate_val,7,6)
        self.fupdate_val.clicked.connect(self.update_setfio2)
        self.f_en = True
        
    def update_setfio2(self):
        global fio_val
        try:
            self.lfio2.setText(self.fio2_v)
            fio_val = int(self.lfio2.text())
            print('update fio2',fio_val)
        except:
            v = self.fio2label.text()
            self.lfio2.setText(v)
        fio_val = int(self.lfio2.text())
        self.slfio2.deleteLater()
        self.fio2label.deleteLater()
        self.fupdate_val.deleteLater()
        self.f_en = False
        #self.update_parameters()
    
    def fio2updateLabel(self, value):      
        self.fio2label.setText(str(value))
        #self.lfio2.setText(str(value))
        self.fio2_v = str(value)     
        
    def value_set(self):
       
        self.sl = QSlider(Qt.Vertical, self) 
        self.sl.setRange(0, 100)
        self.sl.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        self.sl.setFocusPolicy(Qt.NoFocus)
        self.sl.setPageStep(5)
        self.sl.valueChanged.connect(self.updateLabel)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(5)

        self.label = QLabel('0', self)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.label.setMinimumWidth(80)
        self.label.setFont(QFont('Arial', 25))
        self.label.setStyleSheet("color: white;  background-color: black")

        self.layout.addWidget( self.sl,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.label,6,6)

        self.update_val = QPushButton('Update')
        self.update_val.setFont(QFont('Arial', 20))  
        self.update_val.setStyleSheet("background-color: red")
        self.layout.addWidget(self.update_val,7,6)
        self.update_val.clicked.connect(self.update_set)    
    
    def volume_set(self):
       
        self.slv = QSlider(Qt.Vertical, self)
        self.slv.setRange(50, 1500)
        self.slv.setStyleSheet("QSlider{min-width: 100px; max-width: 100px;} QSlider::groove:vertical{border: 1px solid #262626; width: 30px; background: grey; margin: 0 12px;} QSlider::handle:vertical {background: white; border: 2px #55F4A5; width: 40px; height: 50px; line-height: 20px;margin-top: -4px; margin-bottom: -4px; border-radius: 9px;}") 
        self.slv.setFocusPolicy(Qt.NoFocus)
        v = self.lvol.text()
        self.slv.setValue(int(v))
        self.slv.setPageStep(5)
        self.slv.setGeometry(QtCore.QRect(390,300,360,36))
        self.slv.valueChanged.connect(self.volume_update)
        self.slv.setTickPosition(QSlider.TicksBelow)
        self.slv.setTickInterval(5)

        self.vlabel = QLabel(v, self)
        self.vlabel.setAlignment(Qt.AlignRight | Qt.AlignRight)
        self.vlabel.setMinimumWidth(80)
        self.vlabel.setFont(QFont('Arial', 25))
        self.vlabel.setStyleSheet("color: white;  background-color: black")

        self.layout.addWidget( self.slv,2,6,4,1,alignment=Qt.AlignRight)
        self.layout.addWidget(self.vlabel,6,6)

        self.vupdate_val = QPushButton('Vol update')
        self.vupdate_val.setFont(QFont('Arial', 13))  
        self.vupdate_val.setStyleSheet("background-color: red")
        self.layout.addWidget(self.vupdate_val,7,6)
        self.vupdate_val.clicked.connect(self.lvolume_set)
        self.v_en = True
        
    def update_set(self):
        global pressure_val,volume_val,fio_val,peep_val
 #       print('pink',self.updated_value) #Updated value
        if (self.pressure_value == True):
            self.lpressure.setText(self.updated_value)
            pressure_val = int(self.lpressure.text())
            self.pressure_value = False
        if (self.volume_value == True):
            self.lvol.setText(self.updated_value)
            volume_val = int(self.lvol.text())
            self.volume_value = False
        if(self.bpm_value == True):
            self.lbpm.setText(self.updated_value)
            self.bpm_value = False
        if(self.fio2_value == True):
            self.lfio2.setText(self.updated_value)
            fio_val = self.lfio2.text()
            self.fio2_value = False
        if(self.peep_value == True):
            self.lpeep.setText(self.updated_value)
            a = self.lpeep.text()
    #        print('')
            peep_val = int(self.lpeep.text())
            self.peep_value == False
        print('update_vol',volume_val)
        print('update_pre',pressure_val)
        print('update_fio2',fio2_value)
        print('update_peep',peep_val)
        self.sl.deleteLater()
        self.label.deleteLater()
        self.update_val.deleteLater()
        self.update_parameters()
        self.v_en = False
    
        
    def volume_update(self, value):
        self.vlabel.setText(str(value))
        self.vol_v = str(value)
        
    def lvolume_set(self):
        global volume_val
        #print(self.updated_value) #Updated value
        try:
            self.lvol.setText(self.vol_v)
            volume_val = int(self.lvol.text())
            self.slv.deleteLater()
            print('update vol',volume_val)
        except:
            v = self.vlabel.text()
            self.lvol.setText(v)
            volume_val = int(self.lvol.text())
#        print('volume')
        self.slv.deleteLater()
        self.vlabel.deleteLater()
        self.vupdate_val.deleteLater()
        self.update_parameters()
        self.v_en = False
    
    def bpm_update(self):
        self.bpm_value = True

    def fio2_update(self):
        self.fio2_value = True

    def peep_update(self):
        self.peep_value = True    

    def pressure_update(self):
        self.pressure_value = True

    def volume_updates(self):
        self.volume_value = True      
        
    def updateLabel(self, value):      
        self.label.setText(str(value))
        self.updated_value = str(value)

        
    def ie_update(self):

      self.cb = QComboBox()
      self.cb.addItem("IE Values")
      self.cb.addItem("1:1")
      self.cb.addItem("1:2")
      self.cb.addItem("1:3")
      self.cb.addItem("1:4")
      self.cb.setFont(QFont('Arial', 20))
      self.cb.setStyleSheet("color: black;  background-color: white") 
      self.cb.setGeometry(200, 150, 120, 40)  
      self.layout.addWidget(self.cb,7,4)
      self.cb.currentIndexChanged.connect(self.ie_updated)

    def es_update(self):
        self.bes.showPopup()
        
    def es_value(self,value):
        global es,pressure_val
        
        if(value == 1):
            es = (5*pressure_val)/100
        if(value == 2):
            es = (10*pressure_val)/100
        if(value == 3):
            es = (15*pressure_val)/100
        if(value == 4):
            es = (20*pressure_val)/100           
        if(value == 5):
            es = (25*pressure_val)/100
        if(value == 'None'):
            es = 8
#        print('es_set',value)
#        print('es',es)
    def ie_updated(self, value):
        #self.cb.deleteLater()
        global ie_value
        self.ie_value = str(value)
        ie_value = int(value)
   #     print('iev',self.ie_value)
        if(value == 1):
            self.lbrdata.setText("1:1")
        if(value == 2):
            self.lbrdata.setText("1:2")
        if(value == 3):
            self.lbrdata.setText("1:3")
        if(value == 4):
            self.lbrdata.setText("1:4")    
        print('ie',value)
                

    def trigger_update(self):

      self.cbtr = QComboBox()
      self.cbtr.addItem("Trigger")
      self.cbtr.addItem("-8")
      self.cbtr.addItem("-7")
      self.cbtr.addItem("-6")
      self.cbtr.addItem("-5")
      self.cbtr.addItem("-4")
      self.cbtr.addItem("-3")
      self.cbtr.addItem("-2")
      self.cbtr.addItem("-1")
      self.cbtr.setFont(QFont('Arial', 20))
      self.cbtr.setStyleSheet("color: black;  background-color: white") 
      self.cbtr.setGeometry(200, 150, 120, 40)  
      self.layout.addWidget(self.cbtr,5,4)
      self.cbtr.currentIndexChanged.connect(self.trigger_updated)

    def trigger_updated(self, value):
        #self.cbtr.deleteLater()
                                        
        global trigger_data
        if value == 1:
            trigger_data = -8
        if value == 2:
            trigger_data = -7
        if value == 3:
            trigger_data = -6
        if value == 4:
            trigger_data = -5
        if value == 5:
            trigger_data = -4
        if value == 6:
            trigger_data = -3
        if value == 7:
            trigger_data = -2
        if value == 8:
            trigger_data = -1    
        #trigger_data = int(self.ltrigger.text())
#        print('t_da8a',trigger_data)                                
        #print(self.trigger_value)
        

    def mode_update(self):

      self.md = QComboBox()
      list = ["VC","PC","SPONT+PS","HFONC","BiPAP"]
      self.md.addItems(list)
#      self.md.addItem("Modes")
#      self.md.addItem("None")
      #self.md.addItem("PRVC")
#      self.md.addItem("VC")
#      self.md.addItem("PC")
#      self.md.addItem("SPONT+PS")
#      self.md.addItem("HFONC")
#      self.md.addItem("BiPAP")
      self.md.setFont(QFont('Arial', 20))
      self.md.setStyleSheet("color: black;  background-color: white") 
      self.md.setGeometry(200, 150, 120, 40)  
      self.layout.addWidget(self.md,3,4)
      self.md.currentIndexChanged.connect(self.mode_updated)

    def mode_updated(self, value):
        global mod_val,graph
        #self.md.deleteLater()
        self.mode_set = int(value)+2
        print('mod_set',self.mode_set)
        if self.mode_set in [0,1]:
         #   self.lmode.setText('None')
#            self.Bstart.setEnabled(False)
            self.bes.hide()
            self.BEs.setVisible(False)
            self.Bpressure.setEnabled(False)
            self.lpressure.setVisible(False)
            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(False)
            self.lvol.setVisible(False)
            self.Bbpm.setEnabled(False)
            self.lbpm.setVisible(False)
            self.Bpeep.setEnabled(False)
            self.lpeep.setVisible(False)
            self.Bfio2.setEnabled(False)
            self.lfio2.setVisible(False)
            self.Bpressure.setText('Pressure')
            print('mode_val',mod_val)
        if self.mode_set == 2:
          #  self.lmode.setText('VC')
            
            mod_val = 1
            self.bes.hide()
#            self.Bstart.setEnabled(True)
            self.BEs.setVisible(False)
            self.Bpressure.setEnabled(False)
            self.lpressure.setVisible(False)
            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(True)
            self.lvol.setVisible(True)
            self.Bbpm.setEnabled(True)
            self.lbpm.setVisible(True)
            self.Bpeep.setEnabled(True)
            self.lpeep.setVisible(True)            
            self.Bfio2.setEnabled(True)
            self.lfio2.setVisible(True)
            self.Bpressure.setText('Pressure')
            self.vc()
            print('mode_val',mod_val)
        if self.mode_set == 3:
           # self.lmode.setText('PC')
            mod_val = 2
 #           self.Bstart.setEnabled(True)
            self.Bpressure.setText('Ps')
            self.BEs.setVisible(False)
            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(False)
            self.lvol.setVisible(False)
            self.Bbpm.setEnabled(True)
            self.lbpm.setVisible(True)
            self.Bpeep.setEnabled(True)
            self.lpeep.setVisible(True)
            self.Bfio2.setEnabled(True)
            self.lfio2.setVisible(True)
            print('mode_val',mod_val)
            self.pc()
        if self.mode_set == 4:
            self.ps()
            #self.lmode.setText('SPONT+PS')
            mod_val = 4
#            self.Bstart.setEnabled(True)
#            self.bes.showPopup()
            self.BEs.setVisible(True)
            self.Bpressure.setEnabled(True)
            self.lpressure.setVisible(True)
            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(False)
            self.lvol.setVisible(False)
            self.Bbpm.setEnabled(False)
            self.lbpm.setVisible(False)
            self.Bpeep.setEnabled(True)
            self.lpeep.setVisible(True)
            self.Bfio2.setEnabled(True)
            self.lfio2.setVisible(True)
            self.Bpressure.setText('PS')
            self.lmvd.setText('-')
            self.lbvedata.setText('0')
            self.lbvedata.setText('0')
            print('mode_val',mod_val)
        if self.mode_set == 5:
            self.hfonc()
            #self.lmode.setText('HFONC')
            mod_val = 5
#            self.Bstart.setEnabled(True)
            self.bes.hide()
            self.BEs.setVisible(False)
            self.Bpressure.setText('Flow')

            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(False)
            self.lvol.setVisible(False)
            self.Bbpm.setEnabled(False)
            self.lbpm.setVisible(False)
            self.Bpeep.setEnabled(False)
            self.lpeep.setVisible(False)
            self.Bfio2.setEnabled(True)
            self.lfio2.setVisible(True)
            print('mode_val',mod_val)
            
        if self.mode_set == 6:
            #self.lmode.setText('BiPAP')
            mod_val = 4
#            self.Bstart.setEnabled(True)
#            self.bes.showPopup()
            self.BEs.setVisible(True)
            self.lpressure.setVisible(True)
            self.Bti.setEnabled(False)
            self.Bvol.setEnabled(False)
            self.lvol.setVisible(False)
            self.Bbpm.setEnabled(True)
            self.lbpm.setVisible(True)
            self.Bpeep.setEnabled(True)
            self.lpeep.setVisible(True)
            self.Bfio2.setEnabled(True)
            self.lfio2.setVisible(True)
            self.Bpressure.setText('PS')
            self.lmvd.setText('-')
            self.lbvedata.setText('0')
            self.lbvedata.setText('0')
            self.Bpressure.setText('PS')
            print('mode_val',mod_val)
    def on_process(self):
   #     print("pressed start button")
    #    dataFetched = self.fetchData()
    #    self.beThread.dataUpdate = dataFetched
        self.alarm.setVisible(True)
        self.fetch_data()
        self.bthThread.update_pwm_Data()
        
        self.beThread.running = True
        self.bthThread.running = True
  #      self.disableUI()
        self.beThread.start()
        self.bthThread.start()
        self.on = 1

        
    def off_process(self):
        global emergency
  #      print("pressed stop button")
#        self.item = ''
#        self.md.setCurrentText(self.item)
        self.alarm.setVisible(False)
        self.alarm.setText('-')
        self.alarm.setStyleSheet("color: white;  background-color: black")
        emergency = 0
#        self.lbvedata.setText('0')
#        self.lbvedata.setText('0')
     #   print('done')
        self.on = 0
        self.beThread.stopSignal.emit()
        self.bthThread.stopSignal.emit()
#        GPIO.output(14,GPIO.HIGH)
#        GPIO.output(26,GPIO.LOW)
        
        
    def createGridLayout(self):
        global lpressure
        global pressure_val,volume_val,fio_val,peep_val,bpm_val
        self.horizontalGroupBox = QGroupBox() 
        self.layout = QGridLayout()
        self.layout.setColumnStretch(6, 9)
        self.layout.setColumnStretch(6, 9)     

        #Adding push buttons
        self.Bpressure = QPushButton(self)
        self.Bpressure.setText('pressure')#pressurepush button
        self.Bpressure.setGeometry(0, 0, 100, 40)
        self.Bpressure.setFont(QFont('Arial', 20))  
        self.Bpressure.setStyleSheet("background-color: white")
        self.Bpressure.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.Bpressure.setEnabled(False)
        self.layout.addWidget(self.Bpressure,8,0)
        
        self.Rgraph = QPushButton('Refresh Graph') #GraphRefreshbutton
        self.Rgraph.setGeometry(0, 0, 100, 40)
        self.Rgraph.setFont(QFont('Arial', 15))  
        self.Rgraph.setStyleSheet("background-color: white")
        self.Rgraph.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Rgraph,7,0)
        self.Rgraph.clicked.connect(self.graph)
        
        self.Bpressure.clicked.connect(self.pressure_set)
        self.Bpressure.clicked.connect(self.pressure_update)

        self.lpressure = QLabel("0")  #pressure label
        self.lpressure.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lpressure.setFont(QFont('Arial', 25))
        self.lpressure.setStyleSheet("color: white;  background-color: black")
 #       
        a = str(self.settings["pressure"]["default"])
        self.lpressure.setText(a)
        pressure_val = int(self.lpressure.text())
        self.layout.addWidget(self.lpressure,9,0)
        
        self.Bvol = QPushButton('Volume') #volumePushButton
        self.Bvol.setGeometry(0, 0, 100, 40)
        self.Bvol.setFont(QFont('Arial', 20))
        self.Bvol.setStyleSheet("background-color: white")
        self.Bvol.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bvol,8,1)
        #Bvol.clicked.connect(self.volume_update)
        self.Bvol.clicked.connect(self.volume_set)
        self.Bvol = QPushButton('Volume') #volumePushButton
        self.Bvol.setGeometry(0, 0, 100, 40)
        self.Bvol.setFont(QFont('Arial', 20))
        self.Bvol.setStyleSheet("background-color: white")
        self.Bvol.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bvol,8,1)
        #Bvol.clicked.connect(self.volume_update)
        self.Bvol.clicked.connect(self.volume_set)        
 

        self.BEs = QPushButton('Es %') #GraphRefreshbutton
        self.BEs.setGeometry(0, 0, 100, 40)
        self.BEs.setFont(QFont('Arial', 15))  
        self.BEs.setStyleSheet("background-color: white")
        self.BEs.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.BEs,8,1)
        self.BEs.clicked.connect(self.es_update)
        self.BEs.clicked.connect(self.es_value)
 
 
        self.lvol = QLabel("0")  #volume label
        self.lvol.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lvol.setFont(QFont('Arial', 25))
        self.lvol.setStyleSheet("color: white;  background-color: black")
        a = str(self.settings["volume"]["default"])
        self.lvol.setText(a)
        volume_val = int(self.lvol.text())
        print('volume_set',volume_val)
        self.layout.addWidget(self.lvol,9,1)
  
        self.Bbpm = QPushButton('BPM')  #BPM PushButton
        self.Bbpm.setGeometry(0, 0, 100, 40)
        self.Bbpm.setFont(QFont('Arial', 20))
        self.Bbpm.setStyleSheet("background-color: white")
        self.Bbpm.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bbpm,8,2)
        self.Bbpm.clicked.connect(self.bpm_set)
        self.Bbpm.clicked.connect(self.bpm_update)

        self.lbpm = QLabel("0")  #BPM label
        self.lbpm.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbpm.setFont(QFont('Arial', 25))
        self.lbpm.setStyleSheet("color: white;  background-color: black")
        a = str(self.settings["bpm"]["default"])
        self.lbpm.setText(a)
        bpm_val = int(self.lbpm.text())
        self.layout.addWidget(self.lbpm,9,2)

        self.Bpeep = QPushButton('PEEP')  #peep_button
        self.Bpeep.setGeometry(0, 0, 100, 40)
        self.Bpeep.setFont(QFont('Arial', 20))  
        self.Bpeep.setStyleSheet("background-color: white")
        self.Bpeep.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bpeep,8,3)
        self.Bpeep.clicked.connect(self.peep_set)
        self.Bpeep.clicked.connect(self.peep_update)

        self.lpeep = QLabel("0")  #peep label
        self.lpeep.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lpeep.setFont(QFont('Arial', 25))
        self.lpeep.setStyleSheet("color: white;  background-color: black")
        a = str(self.settings["peep"]["default"])
        self.lpeep.setText(a)
        peep_val = int(self.lpeep.text())
        self.layout.addWidget(self.lpeep,9,3)

        self.Bfio2 = QPushButton('fio2')  #fio2 Button
        self.Bfio2.setGeometry(0, 0, 100, 40)
        self.Bfio2.setFont(QFont('Arial', 20))
        self.Bfio2.setStyleSheet("background-color: white")
        self.Bfio2.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bfio2,8,4)
        self.Bfio2.clicked.connect(self.fio2_set)
        self.Bfio2.clicked.connect(self.fio2_update)
#        Bfio2.clicked.connect(self.graph)

        self.lfio2 = QLabel("0")  #fio2 label
        self.lfio2.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lfio2.setFont(QFont('Arial', 25))
        self.lfio2.setStyleSheet("color: white;  background-color: black")
        a = str(self.settings["fio2"]["default"])
        self.lfio2.setText(a)
        fio_val = int(self.lfio2.text())
        self.layout.addWidget(self.lfio2,9,4)
        
        self.Bti = QPushButton('Ti')  #ti Button
        self.Bti.setGeometry(0, 0, 100, 40)
        self.Bti.setFont(QFont('Arial', 20))
        self.Bti.setStyleSheet("background-color: white")
        self.Bti.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        self.layout.addWidget(self.Bti,8,5)
        self.Bti.clicked.connect(self.ti_set)
        self.Bti.setEnabled(False)
        #Bti.clicked.connect(self.ti_update)

        self.ti = QLabel("0")  #ti label
        self.ti.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.ti.setFont(QFont('Arial', 25))
        self.ti.setStyleSheet("color: white;  background-color: black")
        #a = str(self.settings["fio2"]["default"])
        #self.lfio2.setText(a)
        #io_val = int(self.lfio2.text())
        self.layout.addWidget(self.ti,9,5)

        Bmode = QPushButton('Mode') #mode button
        Bmode.setGeometry(0, 0, 100, 400)
        Bmode.setFont(QFont('Arial', 20))
        Bmode.setStyleSheet("background-color: white")
   #     self.layout.addWidget(Bmode,3,4)
        self.mode_update()
     #   Bmode.clicked.connect(self.mode_update)

        Btrigger = QPushButton('Trigger')  #trigger button
        Btrigger.setGeometry(0, 0, 100, 40)
        Btrigger.setFont(QFont('Arial', 20))
        Btrigger.setStyleSheet("background-color: white")
        self.trigger_update()
        #self.layout.addWidget(Btrigger,4,4)
        #Btrigger.clicked.connect(self.trigger_update)

        self.ltrigger = QLabel("Trigger")  #trigger label
        self.ltrigger.setFont(QFont('Arial', 25))
        self.ltrigger.setStyleSheet("color: white;  background-color: black")
        self.layout.addWidget(self.ltrigger,4,4)

        self.BIE = QPushButton('I:E')    #IE button
        self.BIE.setGeometry(0, 0, 100, 40)
        self.BIE.setFont(QFont('Arial', 20))
        self.BIE.setStyleSheet("background-color: white")
        self.ie_update()
        #self.layout.addWidget(self.BIE,6,4)
        #self.BIE.clicked.connect(self.ie_update)

        self.lie = QLabel("IE")  #IE label
        self.lie.setFont(QFont('Arial', 25))
        self.lie.setStyleSheet("color: white;  background-color: black")
        self.layout.addWidget(self.lie,6,4)

        self.lmode = QLabel("-")  #mode label
        self.lmode.setFont(QFont('Arial', 25))
        self.lmode.setStyleSheet("color: white;  background-color: black")
        self.layout.addWidget(self.lmode,2,4)

        ratio = '1:2'                  #breath ratio label
        lbr = QLabel('Breath Ratio')
        lbr.setFont(QFont('Arial', 20))
        self.lbrdata = QLabel(ratio)
        self.lbrdata.setFont(QFont('Arial', 25))
        lbr.setStyleSheet("color: white;  background-color: black")
        self.lbrdata.setStyleSheet("color: white;  background-color: black; border: 2px white")
        lbr.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbrdata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbr,2,5)
        self.layout.addWidget(self.lbrdata,3,5)

        pip = '0'                      #pip label       
        lbP = QLabel('PIP')
        lbP.setFont(QFont('Arial', 20))
        self.lbpdata = QLabel(pip)
        self.lbpdata.setFont(QFont('Arial', 25))
        lbP.setStyleSheet("color: #55F4A5;  background-color: black")
        self.lbpdata.setStyleSheet("color: #55F4A5;  background-color: black")
        lbP.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbpdata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbP,4,5)
        self.layout.addWidget(self.lbpdata,5,5)

        pmean = '0'                      #mean label    
        lbpmean = QLabel('P Mean')
        lbpmean.setFont(QFont('Arial', 20))
        self.lbpmeandata = QLabel(pmean)
        self.lbpmeandata.setFont(QFont('Arial', 25))
        lbpmean.setStyleSheet("color: white;  background-color: black")
        self.lbpmeandata.setStyleSheet("color: white;  background-color: black")
        lbpmean.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbpmeandata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbpmean,6,5)
        self.layout.addWidget(self.lbpmeandata,7,5)

        ti = '0'                          #Ti label
        lbti = QLabel('Ti')
        lbti.setFont(QFont('Arial', 20))
        self.lbtidata = QLabel(ti)
        self.lbtidata.setFont(QFont('Arial', 25))
        lbti.setStyleSheet("color: #55F4A5;  background-color: black")
        self.lbtidata.setStyleSheet("color: #55F4A5;  background-color: black")
        lbti.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbtidata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbti,2,6)
        self.layout.addWidget(self.lbtidata,3,6)

        ca = 'Exhale'                      #current activity label
        lbca = QLabel('Current Activity')
        lbca.setFont(QFont('Arial', 20))
        self.lbcadata = QLabel(ca)
        self.lbcadata.setFont(QFont('Arial', 25))
        lbca.setStyleSheet("color: #55F4A5;  background-color: black")
        self.lbcadata.setStyleSheet("color: #55F4A5;  background-color: black")
        lbca.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbcadata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        #self.layout.addWidget(lbca,2,6)
        #self.layout.addWidget(self.lbcadata,3,6)

        Ve = '0'                           #Ve label
        lbve = QLabel('VTi')
        lbve.setFont(QFont('Arial', 20))
        self.lbvedata = QLabel(Ve)
        self.lbvedata.setFont(QFont('Arial', 25))
        lbve.setStyleSheet("color: white;  background-color: black")
        self.lbvedata.setStyleSheet("color: white;  background-color: black")
        lbve.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbvedata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbve,4,6)
        self.layout.addWidget(self.lbvedata,5,6)

        rr = '0'                            #mV label
        lbrr = QLabel('mV')
        lbrr.setFont(QFont('Arial', 20))
        self.lbrrdata = QLabel(rr)
        self.lbrrdata.setFont(QFont('Arial', 25))
        lbrr.setStyleSheet("color: #55F4A5;  background-color: black")
        self.lbrrdata.setStyleSheet("color: #55F4A5;  background-color: black")
        lbrr.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbrrdata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbrr,6,6)
        self.layout.addWidget(self.lbrrdata,7,6)

        peep = '0'                            #PEEP label
        lbpeep = QLabel('PEEP')
        lbpeep.setFont(QFont('Arial', 20))
        self.lbpeepdata = QLabel(peep)
        self.lbpeepdata.setFont(QFont('Arial', 25))
        lbpeep.setStyleSheet("color: white;  background-color: black")
        self.lbpeepdata.setStyleSheet("color: white;  background-color: black")
        lbpeep.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.lbpeepdata.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(lbpeep,8,6)
        self.layout.addWidget(self.lbpeepdata,9,6)
      
        self.Bstart = QPushButton('Start')          #start button
        self.Bstart.setFont(QFont('Arial', 20))
        self.Bstart.setStyleSheet("background-color: white; border-style: outset; border-width: 2px; border-radius: 15px; border-color: #55F4A5; padding: 4px;")
        #Bstart.setStyleSheet("border-style: outset")
        #Bstart.setStyleSheet("border-colour: black")
        #Bstart.setStyleSheet("padding: 4px")
        self.Bstart.clicked.connect(self.on_process)
        self.layout.addWidget(self.Bstart,1,6)
        self.Bstart.clicked.connect(self.stop)
        
        self.lalarm = QLabel('Alarm')
        self.lalarm.setFont(QFont('Arial', 20))
        self.lalarm.setStyleSheet("color: white;  background-color: black")
        self.lalarm.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lalarm,0,0)
        self.alarm = QLabel('-')
        self.alarm.setFont(QFont('Arial', 20))
        self.alarm.setStyleSheet("color: white;  background-color: black")
        self.layout.addWidget(self.alarm,1,0)
        
        

         
        self.lgas = QLabel('Air-Pr')
        self.lgas.setFont(QFont('Arial', 20))
        self.lgas.setStyleSheet("color: white;  background-color: black")
        self.lgas.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lgas,0,1)

        self.lgasd = QLabel('Normal')
        self.lgasd.setFont(QFont('Arial', 25))
        self.lgasd.setStyleSheet("color: white;  background-color: green")
        self.lgasd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lgasd,1,1)

        self.lapr = QLabel('O2 %')
        self.lapr.setFont(QFont('Arial', 20))
        self.lapr.setStyleSheet("color: white;  background-color: black")
        self.lapr.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lapr,0,2)

        self.laprd = QLabel('0')
        self.laprd.setFont(QFont('Arial', 25))
        self.laprd.setStyleSheet("color: white;  background-color: green")
        self.laprd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.laprd,1,2)

        self.lpres = QLabel('Pressure')
        self.lpres.setFont(QFont('Arial', 25))
        self.lpres.setStyleSheet("color: white;  background-color: black")
        self.lpres.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lpres,0,4)

        self.lpresd = QLabel('0')
        self.lpresd.setFont(QFont('Arial', 25))
        self.lpresd.setStyleSheet("color: white;  background-color: green")
        self.lpresd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lpresd,1,4)

        self.lmv = QLabel('VTe')
        self.lmv.setFont(QFont('Arial', 20))
        self.lmv.setStyleSheet("color: white;  background-color: black")
        self.lmv.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lmv,0,3)

        self.lmvd = QLabel('0')
        self.lmvd.setFont(QFont('Arial', 25))
        self.lmvd.setStyleSheet("color: white;  background-color: green")
        self.lmvd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lmvd,1,3)


        self.lrr = QLabel('RR')
        self.lrr.setFont(QFont('Arial', 20))
        self.lrr.setStyleSheet("color: white;  background-color: black")
        self.lrr.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lrr,0,5) 

        self.lrrd = QLabel('0')
        self.lrrd.setFont(QFont('Arial', 25))
        self.lrrd.setStyleSheet("color: white;  background-color: green")
        self.lrrd.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lrrd,1,5) 

        self.llogo = QLabel('Bravo...')
        self.llogo.setFont(QFont('Gabriola', 25))
        self.llogo.setStyleSheet("color: maroon;  background-color: black")
        self.llogo.setAlignment(Qt.AlignLeft | Qt.AlignLeft)
        #self.layout.addWidget(self.llogo,9,0) 
  
        
        self.lpower = QLabel('MAIN POWER')
        self.lpower.setFont(QFont('Arail', 18))
        self.lpower.setStyleSheet("color: white;  background-color: green")
        self.lpower.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.layout.addWidget(self.lpower,0,6)

        self.bes = QComboBox()
        self.bes.addItem("ES %")
        self.bes.addItem("5")
        self.bes.addItem("10")
        self.bes.addItem("15")
        self.bes.addItem("20")
        self.bes.addItem("25")
        self.bes.setFont(QFont('Arial', 20))
        self.bes.setStyleSheet("color: black;  background-color: white")
   #     self.bes.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.bes.setGeometry(200, 150, 120, 40)  
        self.layout.addWidget(self.bes,9,1)
        self.bes.currentIndexChanged.connect(self.es_value)
        
        self.horizontalGroupBox.setLayout(self.layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
