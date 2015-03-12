import socket 
from time import sleep
import log
from log import bcolors
from threading import Thread
import datetime
import os


class NewThermometer:
    Device_Category = "THERMOMETER UDP"
    ID_Counter = 0
    
    Default_Verbosity = 0
    Default_Name="NONE"
    Default_IP = "192.168.0.221"
    Default_UDP_Port = 8898
    Default_Message_Delay = 0.005
    Default_Last_Request = "None"
        
    
    def Report (self, _Text, _Level, _Color = log.bcolors.ENDC):
        #Verbosity is cumulative
        #Verbosity 0: No report at all
        #Verbosity 1: Critical Errors and Initialization Operations
        #Verbosity 2: Non Critical Errors
        #Verbosity 3: Important Regular operations
        #Verbosity 4: All operations
        _AutoColor = [log.bcolors.ENDC, log.bcolors.RED, log.bcolors.ORANGE, log.bcolors.BLUE, log.bcolors.GREEN, log.bcolors.ENDC]
        _ComposedMsg = (str(datetime.datetime.now()) + " " + self.Name + " " + str(_Text) + log.bcolors.ENDC)
        
        if (self.Verbosity != 0) and (_Level <= self.Verbosity):
            if (_Color == log.bcolors.ENDC):
                msg = _AutoColor[_Level] + _ComposedMsg
            else: 
                msg = _Color + _ComposedMsg 
            self.Logger.write(msg)
    
    
    def __init__(self, _IP = Default_IP, _Port = Default_UDP_Port, _Name = Device_Category + " " + str(ID_Counter), _Verbosity = Default_Verbosity):
        self.IP = _IP
        self.Port = _Port
        self.Name = _Name
        self.Verbosity = _Verbosity
        self.ResponseStack = []
        self.CurrentTemp = 100.0
        self.TemperatureAdjustment = -8.2
        self.fileHistoryPath = "/var/www/log/" + self.Name + "History.txt"
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)

    
        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        #Make the Socket aware of Multicast traffic
        self.Socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20)
        
        self.thread_UDP_Listener = Thread(target = self.UDP_Listener)
        self.thread_UDP_Listener.daemon = True
        self.thread_UDP_Listener.start()
        
        self.thread_Temperature_Update = Thread(target = self.Temperature_Update)
        self.thread_Temperature_Update.daemon = True
        self.thread_Temperature_Update.start()
        
        self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " @ " + self.IP + ":" + str(self.Port) + " has been created" + log.bcolors.ENDC), 1)
   
    def Temperature_Update(self):
        while True:
            self.GetTemperature()
            self.Report("Get Temperature automatically", 4)
            sleep(1*61)
            
    def UDP_Listener(self):
        while True:
            Response, Sender = self.Socket.recvfrom(40)   
            self.Report(("Response: " + Response), 4)          
            splittedResponse = Response.split(";")
            try:
                if (splittedResponse[1] == 'T'):
                    self.CurrentTemp = float(splittedResponse[2]) + self.TemperatureAdjustment
                    self.RecordStatus()
                    #self.Report(("Current Temperature: " + str(self.CurrentTemp)), 4)
                else:
                    #self.Report(("Not a temperature: " + str(Response)), 4)
                    pass
        
            except:
                self.Report(("Error with the response"), 2)
                        
    
    def GetTemperature(self):
        Get_Message = "GT"
        self.Socket.sendto(Get_Message, (self.IP, self.Port))
     
    def RecordStatus(self):
        NowDate = str(datetime.datetime.now())
        self.Report((" New Temp. Record from " + self.Name + ": " + str(self.CurrentTemp)), 3)
        
        file = open(self.fileHistoryPath, "a+")
        if os.path.isfile(self.fileHistoryPath):
            file.write(NowDate + ";" + str(self.CurrentTemp) + ";\n")
            file.close();
        else:
            self.Report(("ERROR - Cannot open" + self.fileHistoryPath), 1)
        