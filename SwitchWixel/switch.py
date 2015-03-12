import serial
from time import sleep
import log
from log import bcolors
import datetime

On = bytearray(b'\xAE\x00\x00\x00\x00\xEA')
Off = bytearray(b'\xAE\x00\x01\x01\x00\xEA')
RequestIO = bytearray(b'\xAE\x01\xEA')


class NewSwitch:
    Message = Off
    DefaultVerbosity = 0
    Device_Category = "SWITCH"
    Name="NONE"
    RadioChannel = 100
    Current_Relay_0 = 0
    Current_Relay_1 = 0
    Current_Input_0 = 0

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
    
    def __init__(self, _WixelCentral, _RadioChannel = RadioChannel, _Verbosity=DefaultVerbosity, _Name="SWITCH 0"):
        self.Verbosity = _Verbosity
        self.Name = _Name
        self.RadioChannel = _RadioChannel
        self.Radio = _WixelCentral
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
        self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " on "+ self.Radio.Name + " @ " + str(self.RadioChannel) + " has been created" + log.bcolors.ENDC), 1)
        
    
    def Send(self, _Message):
        #ToDo: Change channel only if needed
        self.Radio.ChangeChannel(self.RadioChannel)
        self.Radio.Send(_Message)
        self.Report((self.Name + ": Message sent -> " + str(_Message)), 4)
        
                    
    def RequestIO (self):
        CommsOK = 0
        self.Report("Requesting IO", 4) 
        while CommsOK <= 2:
            self.Send(RequestIO)
            _Response = self.Radio.SP.read(6)
            _ByteResponse = [0,0,-1,-1,-1,0]
            CommsOK = CommsOK + 1
            
            for i in range(0, len(_Response)):
                _ByteResponse[i] = ord(_Response[i])
             
            #print _ByteResponse
                                  
            self.Report(("SWITCH: Raw RESPONSE: " + str(_ByteResponse[0]) + " " + str(_ByteResponse[1]) + " " + str(_ByteResponse[2]) + " " + str(_ByteResponse[3]) + " " + str(_ByteResponse[4]) + " " + str(_ByteResponse[5])), 4)
            
            if (len(_ByteResponse)>=6):
                if (_ByteResponse[0] != 174):
                    self.Report((bcolors.RED + "ERROR 174 not found ->   " + str(_ByteResponse[0]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                    #CommsOK =+ 1
                    
                elif (_ByteResponse[1] != self.RadioChannel):
                    self.Report((bcolors.RED + "ERROR wrong ID ->   " + str(_ByteResponse[1]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                    #CommsOK =+ 1
                    
                elif (_ByteResponse[5] != 234):
                    self.Report((bcolors.RED + "ERROR 234 not found ->   " + str(_ByteResponse[5]) + "    instead. Trying again..." + bcolors.ENDC), 2)
                
                else:   #Good String   
                    try:
                        self.Current_Relay_0 = _ByteResponse[2]
                        self.Current_Relay_1 = _ByteResponse[3]
                        self.Current_Input_0 = _ByteResponse[4]
                                                
                        self.Report((bcolors.GREEN + "RESPONSE OK -> Relay 0: " + str(self.Current_Relay_0) + " Relay 1: " + str(self.Current_Relay_1) + " Input 0: " + str(self.Current_Input_0) + bcolors.ENDC), 4) 
                        #CommsOK = 0 
                        return _ByteResponse
                    
                    except:
                        self.Report((bcolors.GREEN + "ERROR converting response " + bcolors.ENDC), 1)
                        return _ByteResponse
                        #CommsOK =+ 1 
            else:
                self.Report((bcolors.RED + "ERROR incomplete response from SWITCH ->   " + str(_ByteResponse) + "    trying again..." + bcolors.ENDC), 2)
                return _ByteResponse 
                #CommsOK =+ 1
            #Response_str = self.ThermostatSP.flushInput()
            sleep(1) 
            
        self.Report("No Response", 1)
        return _ByteResponse
     
        
    # TODO: Cambiar el Wixel receptor para que acepte 255 valores
    def SetOutput(self, _Relay_0, _Relay_1):
        self.Message[2] = _Relay_0
        self.Message[3] = _Relay_1
        self.Message[4] = 0     #TODO: Hacer algo con esto
        self.Report((self.Name + " SET Relay 0 -> " + str(_Relay_0) + "  Relay 1 -> " + str(_Relay_1)), 3)
        self.Send(self.Message)   
        