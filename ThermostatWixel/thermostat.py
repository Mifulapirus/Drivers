import serial
import datetime
from time import sleep
import log
from log import bcolors
from TempHistory import *
from LightHistory import *
from threading import Thread
import os

class NewThermostat:
    Status = "Off"
    Name="NONE"
    RadioChannel = 128
    Device_Category = "THERMOSTAT" #Name of the category
    
    def Report (self, _Text, _Level, _Color = log.bcolors.ENDC):
        #Verbosity is cumulative
        #Verbosity 0: No report at all
        #Verbosity 1: Critical Errors and Initialization Operations
        #Verbosity 2: Non Critical Errors
        #Verbosity 3: Important Regular operations
        #Verbosity 4: All operations
        _AutoColor = [log.bcolors.ENDC, log.bcolors.RED, log.bcolors.ORANGE, log.bcolors.BLUE, log.bcolors.GREEN, log.bcolors.ENDC]
        _ComposedMsg = (str(datetime.datetime.now()) + " " + self.Name + " " + str(_Text) + "\n\r" + log.bcolors.ENDC)
        
        if (self.Verbosity != 0) and (_Level <= self.Verbosity):
            if (_Color == log.bcolors.ENDC):
                msg = _AutoColor[_Level] + _ComposedMsg
            else: 
                msg = _Color + _ComposedMsg 
            self.Logger.write(msg)
    
    def __init__(self, _WixelCentral, _RadioChannel = 128, _Verbosity=0, _Name="THERMOSTAT 0"):
        self.Verbosity = _Verbosity
        self.Name = _Name
        self.RadioChannel = _RadioChannel
        self.Radio = _WixelCentral
        self.CurrentTemp = 0
        self.CurrentLight = 0
        self.TemperatureThreshold_High = 0.50
        self.TemperatureThreshold_Low = 1.50
        self.TemperatureTarget = 12.00
        self.TemperatureAdjustment = 0
        self.HeaterStatus = "False"
        self.fileLogPath = "/var/www/log/" + self.Name + ".log"
        self.Logger = log.NewLogger(self.fileLogPath)
        
        MinutesArray = 2 
        self.UpdateTemperature()
        print "Inmediate temperature : " + str(self.CurrentTemp)
        
        global fileTempHistory
        
        #Temp History
        if os.path.isfile(fileTempHistoryPath):
            print "--------------------------------"
            print "- Temperature History file FOUND -"
            fileTempHistory = open(fileTempHistoryPath, "a+")
            print "        Name of the file: ", fileTempHistory.name
            print "        Closed or not: ", fileTempHistory.closed
            print "        Opening mode: ", fileTempHistory.mode
            print "        Softspace flag: ", fileTempHistory.softspace
            print "        File Size: ", os.path.getsize(fileTempHistoryPath)
            print "        Number of records: " + str(len(ReadTempHistory()))
            if len(ReadTempHistory()) > 0:
                print "        Last Temperature: " + GetTemp(GetLastTempRecord()) + " taken on " + GetDate(GetLastTempRecord()) + " with Heater: " + GetHeater(GetLastTempRecord())
            fileTempHistory.close();
    
        else:
            print "------------------------------------"
            print "- Temperature History file NOT FOUND -"
            fileTempHistory = open(fileTempHistoryPath, "a+")
        
        
        #Light History
        if os.path.isfile(fileLightHistoryPath):
            print "--------------------------------"
            print "- Light History file FOUND     -"
            fileLightHistory = open(fileLightHistoryPath, "a+")
            print "        Name of the file: ", fileLightHistory.name
            print "        Closed or not: ", fileLightHistory.closed
            print "        Opening mode: ", fileLightHistory.mode
            print "        Softspace flag: ", fileLightHistory.softspace
            print "        File Size: ", os.path.getsize(fileLightHistoryPath)
            print "        Number of records: " + str(len(ReadLightHistory()))
            if len(ReadLightHistory()) > 0:
                print "        Last Light value: " + GetLight(GetLastLightRecord()) + " taken on " + GetDate(GetLastLightRecord())
            fileLightHistory.close();
    
        else:
            print "--------------------------------"
            print "- Light History file NOT FOUND -"
            fileLightHistory = open(fileLightHistoryPath, "a+")
        #Start threads
        thread_UpdateTemp = Thread(target = self.threaded_UpdateTemp)
        thread_UpdateTemp.daemon = True
        thread_UpdateTemp.start()
        
        thread_UpdateLight = Thread(target = self.threaded_UpdateLight)
        thread_UpdateLight.daemon = True
        thread_UpdateLight.start()
        
        thread_TemperatureHistoryRecorder = Thread(target = self.threaded_TemperatureHistoryRecorder)
        thread_TemperatureHistoryRecorder.daemon = True
        thread_TemperatureHistoryRecorder.start()
        
        thread_LightHistoryRecorder = Thread(target = self.threaded_LightHistoryRecorder)
        thread_LightHistoryRecorder.daemon = True
        thread_LightHistoryRecorder.start()
        
        
        thread_HeaterControl = Thread(target = self.threaded_HeaterControl)
        thread_HeaterControl.daemon = True
        thread_HeaterControl.start()
        self.Report((log.bcolors.GREEN + " + NEW " + self.Device_Category + ": " + self.Name + " on "+ self.Radio.Name + " @ " + str(self.RadioChannel) + " has been created" + log.bcolors.ENDC), 1)
        sleep(0.6)
            
    def Send(self, _Message):
        #ToDo: Change channel only if needed
        self.Radio.ChangeChannel(self.RadioChannel)
        self.Radio.Send(_Message)
        self.Report(("Sent -> " + _Message), 4)

    def TurnOn(self):
        self.Send("SA1\n")
        sleep(0.1)
        
    def TurnOff(self):
        self.Send("SA0\n")
        sleep(0.1)
 
    def SetTargetTemp(self, _TargetTemp=13.00, _internalOperation = False):
        self.Send("ST" + str(_TargetTemp) + "\n")
        #Todo: Create a way to request the target temperature
        self.TemperatureTarget = _TargetTemp 
        if (_internalOperation):
            self.Report(("New Temperature set -> " + log.bcolors.GREEN + str(_TargetTemp) + log.bcolors.ENDC), 3, log.bcolors.ORANGE)
        else:
            self.Report(("New Temperature set -> " + log.bcolors.GREEN +str(_TargetTemp) + log.bcolors.ENDC), 1, log.bcolors.ORANGE)
        sleep(0.1) 
    
        
    def RequestTemperature(self):
        CommsOK = 0
        #print "Requesting Temperature"
        while CommsOK <= 2:
            self.Send("GT\n")
            Response_str = self.Radio.SP.readline()
            #print "THERMOSTAT: Raw RESPONSE: " + Response_str
            splittedResponse = Response_str.split(";")
            if (len(splittedResponse)>=3):
                if (splittedResponse[0] != "BGN"):
                    self.Report((bcolors.RED + "ERROR BGN not found ->   " + splittedResponse[0] + "    instead. Trying again..." + bcolors.ENDC), 2)
                    CommsOK = CommsOK + 1
                    
                elif (splittedResponse[1] != "T"):
                    self.Report((bcolors.RED + "ERROR T not found ->   " + splittedResponse[1] + "    instead. Trying again..." + bcolors.ENDC), 2)
                    CommsOK = CommsOK + 1
                    
                elif (splittedResponse[3] != "END"):
                    self.Report((bcolors.RED + "ERROR END not found ->   " + splittedResponse[3] + "    instead. Trying again..." + bcolors.ENDC), 2)
                
                else:   #Good String   
                    try:
                        Response = float(splittedResponse[2])
                        self.Report((bcolors.GREEN + "RESPONSE OK -> " + str(Response) + bcolors.ENDC), 4) 
                        CommsOK = 0 
                        return Response
                    
                    except:
                        self.Report((bcolors.GREEN + "ERROR converting response to float -> " + splittedResponse[2]+ bcolors.ENDC), 2)
                        CommsOK = CommsOK + 1
            else:
                self.Report((bcolors.RED + "ERROR incomplete response from thermostat ->   " + Response_str + "    trying again..." + bcolors.ENDC), 2) 
                CommsOK = CommsOK + 1
            #Response_str = self.ThermostatSP.flushInput()
            sleep(2)
            
        self.Report("No Response", 1)
        return 104
    
    def RequestLight(self):
        CommsOK = 0
        #print "Requesting Temperature"
        while CommsOK <= 2:
            self.Send("GL\n")
            try:
                Response_str = self.Radio.SP.readline()
                
                splittedResponse = Response_str.split(";")
                if (len(splittedResponse)>=3):
                    if (splittedResponse[0] != "BGN"):
                        self.Report(("ERROR BGN not found ->   " + splittedResponse[0] + "    instead. Trying again..."), 2)
                        CommsOK =+ 1
                        
                    elif (splittedResponse[1] != "L"):
                        self.Report(("ERROR L not found ->   " + splittedResponse[1] + "    instead. Trying again..."), 2)
                        CommsOK =+ 1
    
                    elif (splittedResponse[3] != "END"):
                        self.Report(("ERROR END not found ->   " + splittedResponse[3] + "    instead. Trying again..."), 2)
                    
                    else:   #Good String   
                        try:
                            Response = float(splittedResponse[2])
                            self.Report(("RESPONSE OK -> " + str(Response)), 4) 
                            CommsOK = 0 
                            return Response
                        
                        except:
                            self.Report(("ERROR converting response to float -> " + splittedResponse[2]), 2)
                            CommsOK =+ 1 
                else:
                    self.Report(("ERROR incomplete response from thermostat ->   " + Response_str + "    trying again..."), 2) 
                    CommsOK =+ 1
                #Response_str = self.ThermostatSP.flushInput()
                sleep(2)
            except:
                self.Report("Serial buffer is empty", 1)
            
        self.Report("No Response", 1)
        return 0
        
    def UpdateTemperature(self):                 #lectura del TC74A7 Direccion 0x4F 
        self.CurrentTemp = self.RequestTemperature() + self.TemperatureAdjustment

        return self.CurrentTemp
    
    def UpdateLight(self):                 #lectura del TC74A7 Direccion 0x4F 
        self.CurrentLight = self.RequestLight()
        return self.CurrentLight

    def threaded_UpdateTemp(self):
        print "THREAD: Update Temp STARTED"
        while 1:
            try:
                self.UpdateTemperature()
                self.SetTargetTemp(self.TemperatureTarget, True)
            except:
                self.Report((str(datetime.datetime.now()) + " ERROR reading temperature"), 2)
            sleep(10)
               
    def threaded_UpdateLight(self):
        print "THREAD: Update Ligh STARTED"
        while 1:
            self.UpdateLight()
            sleep(10)    
            
    def threaded_TemperatureHistoryRecorder(self):
        print "THREAD: Temperature History Recorder STARTED"
        while 1:
            global Temp
            NowDate = str(datetime.datetime.now())
            CurrentTemp_ = str("{0:.2f}".format(self.CurrentTemp))
            #Remember that heater goes inverted
            NewRecord = [NowDate, CurrentTemp_, self.HeaterStatus, str(self.TemperatureTarget), str(self.TemperatureThreshold_High), str(self.TemperatureThreshold_Low)]
            self.Report((" New Temp. Record: " + NewRecord[1] + ";" + NewRecord[2] + ";" + NewRecord[3] + ";" + NewRecord[4]+ ";" + NewRecord[5]), 3)
            if os.path.isfile(fileTempHistoryPath):
                fileTempHistory = open(fileTempHistoryPath, "a+")
                fileTempHistory.write(NewRecord[0] + ";" + NewRecord[1] + ";" + NewRecord[2] + ";" + NewRecord[3] + ";" + NewRecord[4] + ";" + NewRecord[5] + ";\n")
                fileTempHistory.close();
            else:
                print "ERROR - Temperature History File NOT FOUND"
            sleep (60)

    def threaded_LightHistoryRecorder(self):
        print "THREAD: Light History Recorder STARTED"
        while 1:
            #global CurrentLight
            #try:
            NowDate = str(datetime.datetime.now())
            #Remember that heater goes inverted
            NewRecord = [NowDate, str(self.UpdateLight())]
            self.Report((" New Light. Record: " + NewRecord[1]), 3)
            if os.path.isfile(fileLightHistoryPath):
                fileLightHistory = open(fileLightHistoryPath, "a+")
                fileLightHistory.write(NewRecord[0] + ";" + NewRecord[1] + ";\n")
                fileLightHistory.close();
            else:
                self.Report("ERROR - Light History File NOT FOUND", 1)
            sleep (60.437)
            #except:
            #    print "ERROR - writing on Light History File"
    
    def threaded_HeaterControl(self):
        self.HeaterStatus
        print "THREAD: Heater Control STARTED"
        print "        Target Temperature: " + str(self.TemperatureTarget)
        print "        Temperature Threshold High: " + str(self.TemperatureThreshold_High)
        print "        Temperature Threshold Low: " + str(self.TemperatureThreshold_Low)
        print "        Current Temperature: " + str(self.CurrentTemp)
        
        while 1:
            PreviousHeaterStatus = self.HeaterStatus
            if (self.CurrentTemp < (self.TemperatureTarget - self.TemperatureThreshold_Low)):
                self.HeaterStatus = "True"
                self.TurnOn()
                #print "        Heater On - " + str(CurrentTemp)
            elif (self.CurrentTemp > (self.TemperatureTarget + self.TemperatureThreshold_High)):
                self.HeaterStatus = "False"
                self.TurnOff()
                #print "        Heater Off - " + str(CurrentTemp)
            else:   #Temperature in the middle
                if PreviousHeaterStatus == "True":
                    self.HeaterStatus = "True"
                    self.TurnOn()
                else:
                    self.HeaterStatus = "False"
                    self.TurnOff()
            
            
            if PreviousHeaterStatus != self.HeaterStatus:
                self.Report((" Heater Switched to " + self.HeaterStatus), 1, log.bcolors.ORANGE) 
            else:
                self.Report((" Heater remains " + self.HeaterStatus), 3, log.bcolors.GREEN)
                
            #print "    Target Temperature: " + str(TemperatureTarget)
            #print "    Temperature Threshold High: " + str(TemperatureThreshold_High)
            #print "    Temperature Threshold Low: " + str(TemperatureThreshold_Low)
            #print "    Current Temperature: " + str(CurrentTemp) + bcolors.ENDC
            #print "            "    + HeaterStatus
            sleep(1*60)
            #sleep(5)    

if __name__ == "__main__":
    print "This is Thermostat"
    Thermostat = NewThermostat()
    while 1:
        print Thermostat.RequestTemperature()
        Thermostat.TurnOff()
        Thermostat.TurnOn()
