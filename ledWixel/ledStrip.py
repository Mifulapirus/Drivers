import serial
from time import sleep
import log
from log import bcolors
import datetime

Red = bytearray(b'\xAE\x00\x63\x00\x00\xEA')
Green = bytearray(b'\xAE\x00\x00\x63\x00\xEA')
Blue = bytearray(b'\xAE\x00\x00\x00\x63\xEA')
White = bytearray(b'\xAE\x00\x63\x63\x63\xEA')
WhiteLow = bytearray(b'\xAE\x00\x33\x33\x33\xEA')
Black = bytearray(b'\xAE\x00\x00\x00\x00\xEA')
RequestRGB = bytearray(b'\xAE\x01\xEA')


class NewLedStrip:
    Message = Black
    Device_Category = "LED SERIAL"
    Name="NONE"
    RadioChannel = 10

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
    
    
    
    def __init__(self, _WixelCentral, _RadioChannel = 10, _Verbosity=0, _Name="LED STRIP 0"):
        self.Verbosity = _Verbosity
        self.Name = _Name
        self.RadioChannel = _RadioChannel
        self.Radio = _WixelCentral
        self.CurrentRed = 0
        self.CurrentGreen = 0
        self.CurrentBlue = 0
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
        self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " on "+ self.Radio.Name + " @ " + str(self.RadioChannel) + " has been created" + log.bcolors.ENDC), 1)
        
    
    def Send(self, _Message):
        #ToDo: Change channel only if needed
        self.Radio.ChangeChannel(self.RadioChannel)
        self.Radio.Send(_Message)
                    
    def RequestRGB (self):
        CommsOK = 0
        self.Report("Requesting RGB", 4) 
        while CommsOK <= 2:
            self.Send(RequestRGB)
            _Response = self.Radio.SP.read(6)
            _ByteResponse = [0,0,0,0,0,0]
            
            for i in range(0, len(_Response)):
                _ByteResponse[i] = ord(_Response[i])
            
            print _ByteResponse
                                  
            self.Report(("LED: Raw RESPONSE: " + str(_ByteResponse[0]) + " " + str(_ByteResponse[1]) + " " + str(_ByteResponse[2]) + " " + str(_ByteResponse[3]) + " " + str(_ByteResponse[4]) + " " + str(_ByteResponse[5])), 4)
            
            if (len(_ByteResponse)>=6):
                if (_ByteResponse[0] != 174):
                    self.Report((bcolors.RED + "ERROR 174 not found ->   " + str(_ByteResponse[0]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                    CommsOK =+ 1
                    
                elif (_ByteResponse[1] != self.RadioChannel):
                    self.Report((bcolors.RED + "ERROR wrong ID ->   " + str(_ByteResponse[1]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                    CommsOK =+ 1
                    
                elif (_ByteResponse[5] != 234):
                    self.Report((bcolors.RED + "ERROR 234 not found ->   " + str(_ByteResponse[5]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                
                else:   #Good String   
                    try:
                        self.CurrentRed = _ByteResponse[2]
                        self.CurrentGreen = _ByteResponse[3]
                        self.CurrentBlue = _ByteResponse[4]
                                                
                        self.Report((bcolors.GREEN + "RESPONSE OK -> R: " + str(self.CurrentRed) + " G: " + str(self.CurrentG) + " B: " + str(self.CurrentB) + bcolors.ENDC), 4) 
                        CommsOK = 0 
                        return _ByteResponse
                    
                    except:
                        self.Report((bcolors.GREEN + "ERROR converting response " + bcolors.ENDC), 2)
                        CommsOK =+ 1 
            else:
                self.Report((bcolors.RED + "ERROR incomplete response from LED ->   " + str(_ByteResponse) + "    trying again..." + bcolors.ENDC), 2) 
                CommsOK =+ 1
            sleep(2)
            
        self.Report("No Response", 1)
        return 104
        
    # TODO: Cambiar el Wixel receptor para que acepte 255 valores
    def RGB(self, _R, _G, _B):
        if _R >= 99: _R = 90
        if _G >= 99: _G = 90
        if _B >= 99: _B = 90
        
        self.Message[2] = _R
        self.Message[3] = _G
        self.Message[4] = _B
        
        self.Send(self.Message)  
        #self.RequestRGB() 
        
    
    def Red(self, _Brightness):
        self.RGB(_Brightness, 0, 0)
    
    def Green(self, _Brightness):
        self.RGB(0, _Brightness, 0)
    
    def Blue(self, _Brightness):
        self.RGB(0, 0, _Brightness)
    
    def Black(self):
        self.RGB(0, 0, 0)
    