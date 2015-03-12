"""
 Title: maestro6.py
 Description: 
""" 
__author__ = "Angel Hernandez"
__contributors__ = "Angel Hernandez"
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Angel Hernandez"
__email__ = "angel@tupperbot.com"
__status__ = "beta"

import serial
import time

class maestro6:
	DEFAULT_ACCEL = 10
	DEFAULT_SPEED = 30
	def __init__(self, _port='/dev/ttyACM0'):
		print("New Maestro6 @ " + _port)
		usbPort = _port
		self.sc = serial.Serial(usbPort, timeout=1)
		self.defaultSpeed = 30
		self.defaultAccel = 10
	
	def closeServo(self):
		self.sc.close()
		
	def setSpeed(self, channel, speed):
		#Compact protocol: 0x87, channel number, speed low bits, speed high bits
		_speedLow = (speed & 0x7f)
		_speedHigh = ((speed >> 7) & 0x7f)
		_cmd = chr(0x87)+chr(channel)+chr(_speedLow)+chr(_speedHigh)
		self.sc.write(_cmd)
	
	def setAcceleration(self, channel, accel):
		#Compact protocol: 0x89, channel number, acceleration low bits, acceleration high bits
		_low = (accel & 0x7f)
		_high = ((accel >> 7) & 0x7f)
		_cmd = chr(0x89)+chr(channel)+chr(_low)+chr(_high)
		self.sc.write(_cmd)
		
	def servoOff(self, n):
		_cmd = chr(0x84)+chr(n)+chr(0)+chr(0)
		self.sc.write(_cmd)
		
	def setTargetQms(self, channel, target):
		#Compact protocol: 0x84, channel number, target low bits, target high bits
		_targetLow = (target & 0x7f)
		_targetHigh = ((target >> 7) & 0x7f)
		_cmd = chr(0x84)+chr(channel)+chr(_targetLow)+chr(_targetHigh)
		self.sc.write(_cmd)
	
	def setTargetMs(self, channel, targetMS):
		self.setTargetQms(channel, targetMS * 4)
	
	def setPosition(self, channel, position, acceleration = DEFAULT_ACCEL, speed = DEFAULT_SPEED):
		self.setAcceleration(channel, acceleration)
		self.setSpeed(channel, speed)
		self.setTargetQms(channel, position)
		
	def getPosition(self, servo):
		chan  = servo &0x7f
		data =  chr(0xaa) + chr(0x0c) + chr(0x10) + chr(chan)
		self.sc.write(data)
		lowerByte = ord(self.sc.read())
		upperByte = ord(self.sc.read())
		return (upperByte << 8) | (lowerByte & 0xFF)

	def getErrors(self):
		data =  chr(0xaa) + chr(0x0c) + chr(0x21)
		self.sc.write(data)
		w1 = ord(self.sc.read())
		w2 = ord(self.sc.read())
		return w1, w2

	def triggerScript(self, subNumber):
		data =  chr(0xaa) + chr(0x0c) + chr(0x27) + chr(0)
		self.sc.write(data)
		return 1


		
		
