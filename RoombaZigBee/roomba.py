import serial
from time import sleep
import binascii
import log
 
class NewRoomba:
    Status = "Off"
    Device_Category = "VACUUM CLEANER" #Name of the category
    
    def __init__(self, _Name = "Roomba"):
        self.Name = _Name
        self.RoombaSP = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=5)
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
    
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
                
    def Send(self, Data):
        if (self.RoombaSP.isOpen()):
            self.RoombaSP.write(Data)         
        else:
            try:
                self.RoombaSP.open()
                self.Report("Serial port has been open", 4)
                
            except:
                self.Report("Serial port is not connected", 1)

    def Stop(self):
        if (self.Status == "Regular"):
            self.Regular()
        elif (self.Status == "Spot"):
            self.Spot()
        elif (self.Status == "Max"):
            self.Max()
        elif (self.Status == "ForceSeekingDock"):
            self.ForceSeekingDock()
        self.Status = "Off"
                        
    def Start(self):
        #self.RoombaSP.setDTR(0)
        #sleep(2)
        #self.RoombaSP.setDTR(1)
        self.Send(chr(128))
        self.Status = "Started"
        
    
    def Safe(self):
        self.Start()
        self.Send(chr(131))
        self.Status = "Safe"
        
    def Full(self):
        self.Start()
        self.Send(chr(132))
        self.Status = "Full"
    
    def Power(self):
        self.Safe()
        self.Send(chr(133))
        self.Status = "Power"
    
    def Spot(self):
        self.Safe()
        self.Send(chr(134))
        self.Status = "Spot"
        
    def Regular(self):
        self.Safe()
        self.Send(chr(135))
        self.Status = "Regular"
         
    def Max(self):
        self.Safe()
        self.Send(chr(136))
        self.Status = "Max"
        
    def ForceSeekingDock(self):
        self.Safe()
        self.Send(chr(143))
        self.Status = "ForceSeekingDock"
            
    def Beep(self):
        self.Full()
        self.Send([140, 0, 1, 62, 32])
        self.Send([141, 0])
        self.Report("COMMAND: Beep", 4)
        
    def RequestAllSensor(self):
        self.Safe()
        self.Send(chr(142)) #Request Sensors
        self.Send(chr(2))   #All Sensors
        while self.RoombaSP.inWaiting():
            self.Report(self.RoombaSP.read(), 4)
        #print binascii.b2a_hex(Sensors)
        #return Sensors
        #80808080808080fb88


if __name__ == "__main__":
    print "This is Roomba"
    Roomba = NewRoomba()
    Roomba.Regular()
    sleep(2)
    Roomba.Regular()
    print "Requesting All Sensors"
    Roomba.RequestAllSensor()
    #print AllSensors
    print "Done"
    
    