import socket 
from time import sleep
import log
from log import bcolors
from threading import Thread
import datetime
import os


class NewDehumidifier:
    Device_Category = "Dehumidifier UDP"
    ID_Counter = 0
    
    Default_Verbosity = 0
    Default_Name="NONE"
    Default_IP = "192.168.0.221"
    Default_UDP_Port = 8899
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
        self.CurrentPowerStatus = 0
        self.LastPowerStatus = 0
        self.ResponseStack = []
        self.fileDehumHistoryPath = "/var/www/log/" + self.Name + "History.txt"
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
        

        self.Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        #Make the Socket aware of Multicast traffic
        self.Socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20)
        
        self.thread_UDP_Listener = Thread(target = self.UDP_Listener)
        self.thread_UDP_Listener.daemon = True
        self.thread_UDP_Listener.start()
        
        self.thread_PowerStatus_Update = Thread(target = self.PowerStatus_Update)
        self.thread_PowerStatus_Update.daemon = True
        self.thread_PowerStatus_Update.start()
        
        self.thread_Security_Update = Thread(target = self.Security_Update)
        self.thread_Security_Update.daemon = True
        self.thread_Security_Update.start()
        
        self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " @ " + self.IP + ":" + str(self.Port) + " has been created" + log.bcolors.ENDC), 1)
   
    def PowerStatus_Update(self):
        while True:
            self.GetPowerStatus()
            self.Report("Power Status Updated automatically", 4)
            sleep(10)
            
    def Security_Update(self):
        self.Report("Security Update thread started", 3)
        while True:
            try:
                self.SetPowerStatus(self.LastPowerStatus)
                self.Report("Security Update", 4)
                sleep(1*60)
            except:
                self.Report("Error @ security thread, trying again in 5s", 1)
                sleep(5)
            
            
    def UDP_Listener(self):
        while True:
            Response, Sender = self.Socket.recvfrom(40)   
            self.Report(("Response: " + Response), 4)          
            splittedResponse = Response.split(";")
            try:
                if (splittedResponse[1] == 'P'):
                    self.CurrentPowerStatus = int(splittedResponse[2])
                    
                    if (self.LastPowerStatus != self.CurrentPowerStatus): #Status has changed
                        self.RecordStatus()
                        self.LastPowerStatus = self.CurrentPowerStatus
                        self.Report(("Status has changed: " + log.bcolors.GREEN + str(self.CurrentPowerStatus) + log.bcolors.ENDC), 1, log.bcolors.ORANGE)
                    else:
                        self.Report(("Status has not changed: " + str(self.CurrentPowerStatus)), 4)
                else:
                    #self.Report(("Not power: " + str(Response)), 4)
                    pass

            except:
                self.Report(("Error with the response"), 3)
                        
    
    def GetPowerStatus(self):
        Get_Message = "GP"
        self.Socket.sendto(Get_Message, (self.IP, self.Port))
               
     
    def SetPowerStatus(self, _NewPowerStatus):
        Set_Message = "SP" + str(_NewPowerStatus)
        self.Socket.sendto(Set_Message, (self.IP, self.Port))
        self.Report(Set_Message, 4)
        self.GetPowerStatus()
    
    def RecordStatus(self):
        NowDate = str(datetime.datetime.now())
        NewRecord = [NowDate, str(self.CurrentPowerStatus)]
        self.Report((bcolors.BLUE + "New Dehum. Record: " + NewRecord[1] + bcolors.ENDC), 1)
        
        fileDehumHistory = open(self.fileDehumHistoryPath, "a+")
        if os.path.isfile(self.fileDehumHistoryPath):
            fileDehumHistory.write(NewRecord[0] + ";" + NewRecord[1] + ";\n")
            fileDehumHistory.close();
        else:
            print "ERROR - Cannot open" + self.fileDehumHistoryPath
        