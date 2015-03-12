#===============================================================================
# wixelCentral.pg
#
#===============================================================================
 
import serial
from time import sleep
import log
from log import bcolors
import datetime

class NewWixelCentral:
    Verbosity = 0
    Name="NONE"
    RadioChannel = 10
    Device_Category = "RADIO" #Name of the category
    
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
    
    
    def __init__(self, _SP="/dev/ttyACM0", _Baud=9600, _RadioChannel = 10, _Verbosity=0, _Name="WIXEL CENTRAL"):
        self.Verbosity = _Verbosity
        self.Name = _Name
        self.RadioChannel = _RadioChannel
        self.Baud = _Baud
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
        self.Report("Custom port" + _SP, 3)
        
        try:
            self.SP = serial.Serial(_SP, baudrate=_Baud, timeout=1)
            self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " on "+ str(self.SP.port) + " @ " + str(self.Baud) + " has been created" + log.bcolors.ENDC), 1)
            
        except:
            self.SP = serial.Serial()
            self.Report("ERROR: Serial port " + _SP + " not found", 1)


    def Send(self, _Message):
        if (self.SP.isOpen()):
            self.SP.write(_Message)
            self.Report("Message Sent: " + _Message, 4)
            
        else:
            try:
                self.SP.open()
                self.Report("Serial port has been open", 3)
                
            except:
                self.Report("ERROR Serial port is not connected", 1)
    
    
    def ChangeChannel(self, _Channel):
        
        if _Channel != self.RadioChannel:
            self.RadioChannel = _Channel
            _Message = bytearray(b'\xFF\x00')
            _Message[1] = _Channel
            self.Send(_Message)  
            self.Report(("Radio channel has been changed to " + str(_Message[1])), 3)
            sleep(0.05)
            
            
        else:
            self.Report("Same Channel, no need to change", 4)
          
    