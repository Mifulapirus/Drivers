"""
 Title: sabertooth.py
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
from time import sleep

class sabertooth:
	DEFAULT_ACCEL = 10
	DEFAULT_SPEED = 30
	
	def __init__(self, _port='/dev/ttyUSB0'):
		print("New Sabertooth @ " + _port)
		usbPort = _port
		self.sp = serial.Serial(port=usbPort, baudrate=38400, timeout=1)
		self.RIGHT_MOTOR_ID = 0
		self.LEFT_MOTOR_ID = 4
		
		self.FORWARD_CMD = 0
		self.BACKWARDS_CMD = 1
		self.FORWARD_MIXED_CMD = 8
		self.BACKWARDS_MIXED_CMD = 9
		self.TURN_RIGHT_MIXED_CMD = 10
		self.TURN_LEFT_MIXED_CMD = 11
		
		
		self.defaultSpeed = 30
		self.defaultAccel = 10
		self.address = 128
		
		print("Booting up")
		self.sp.write(chr(0xAA))
		sleep(0.5)
		self.sp.write(chr(0xAA))
		sleep(0.5)
		print("Done")
	
	def drive(self, _motorID, _fw_bw, _speed):
		#Check speed limits
		if (_speed > 127): _speed = 127
		elif (_speed < 0): _speed = 0
		
		#check motor ID
		if ((_motorID != self.RIGHT_MOTOR_ID) and (_motorID != self.LEFT_MOTOR_ID)):
			#print("Invalid Motor ID")
			return False
		
		#check _fw_bw
		if ((_fw_bw != self.FORWARD_CMD) and (_fw_bw != self.BACKWARDS_CMD)):
			#print("Invalid Forward/Backwards command")
			return False
		
		#build command
		_cmd = _motorID + _fw_bw
		#build _crc
		_crc = (self.address + _cmd + _speed) & 0x7F
		
		_msg = chr(self.address) + chr(_cmd) + chr(_speed) + chr(_crc)
		self.sp.write(_msg)
		return True

	def driveMixed (self, _cmd, _speed):
		#Check speed limits
		if (_speed > 127): _speed = 127
		elif (_speed < 0): _speed = 0
				
		#build _crc
		_crc = (self.address + _cmd + _speed) & 0x7F
	
		_msg = chr(self.address) + chr(_cmd) + chr(_speed) + chr(_crc)
		self.sp.write(_msg)
		return True
	
	def driveMixedStart(self):
		self.stop()
		
	def stop(self):
		self.driveMixed(self.FORWARD_MIXED_CMD, 0)
		self.driveMixed(self.TURN_LEFT_MIXED_CMD, 0)
	
	def driveForward(self, _speed):
		self.driveMixed(self.FORWARD_MIXED_CMD, _speed)
	
	def driveBackwards(self, _speed):
		self.driveMixed(self.BACKWARDS_MIXED_CMD, _speed)
	
	def driveLeft(self, _speed):
		self.driveMixed(self.TURN_LEFT_MIXED_CMD, _speed)
	
	def driveRight(self, _speed):
		self.driveMixed(self.TURN_RIGHT_MIXED_CMD, _speed)
		

	

if __name__ == "__main__":
	MD = sabertooth()
	_delay = 3

	while 1:
		
		MD.driveForward(10)
		sleep(_delay)
		MD.stop()
		sleep(_delay)
		
		MD.driveBackwards(20)
		sleep(_delay)
		MD.stop()
		sleep(_delay)

