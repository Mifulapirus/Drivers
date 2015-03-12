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

class sabertoothSimplified:
	#Driver must be configures as
	#	1	2	3	4	5	6
	#	ON	OFF	OFF	OFF	ON	ON
	
	def __init__(self, _port='/dev/ttyUSB0'):
		usbPort = _port
		self.sp = serial.Serial(port=usbPort, baudrate=9600, timeout=1)
				
		self._CMD_STOP = 0
			
		self._MOTOR_A_ID = 0
		self._CMD_MOTOR_A_FULL_REVERSE = 1
		self._CMD_MOTOR_A_STOP = 64
		self._CMD_MOTOR_A_FULL_FORWARD = 127
		
		self._MOTOR_B_ID = 1
		self._CMD_MOTOR_B_FULL_REVERSE = 128
		self._CMD_MOTOR_B_STOP = 192
		self._CMD_MOTOR_B_FULL_FORWARD = 255
		
		self._RIGHT_MOTOR_ID = 0
		self._LEFT_MOTOR_ID = 1
		
		self._FORWARD = 0
		self._REVERSE = 1 
	
	def wakeUp(self):
		self.driveMotor(self._MOTOR_A_ID, self._FORWARD, self._CMD_MOTOR_A_STOP+1)
		self.driveMotor(self._MOTOR_B_ID, self._FORWARD, self._CMD_MOTOR_A_STOP+1)
		
		
	def stop(self):
		self.sp.write(chr(self._CMD_STOP))
		print ("CMD: " + str(self._CMD_STOP))
	
	#_MotorID should be 0 for motor A or 1 for motor BACKWARDS_CMD
	#_speed is the percentage of the current direction
	# 0: Stop
	# 1-127: Motor A
	# 	1-63: Full Reverse
	#	64: Stop
	#	65-127: Full Forward
	# 128-255: Motor B
	# 	128-191: Full Reverse
	#	192: Stop
	#	193-255: Full Forward
	def driveMotor(self, _motorID, _direction, _speed):
		if _speed > 100: _speed = 100
		elif _speed < 0: _speed = 0
		_factor = -1.0
		if (_motorID == self._MOTOR_A_ID):
			if (_speed == 0):
				_cmd = self._CMD_MOTOR_A_STOP
			else:
				if (_direction == self._REVERSE): #Range between 1-63
					_factor = (self._CMD_MOTOR_A_STOP - 1 - self._CMD_MOTOR_A_FULL_REVERSE) / 100.0
					_cmd = self._CMD_MOTOR_A_STOP - 1 - int(_speed * _factor)
				elif (_direction == self._FORWARD): #Range between 65-127
					_factor = (self._CMD_MOTOR_A_FULL_FORWARD - self._CMD_MOTOR_A_STOP - 1) / 100.0
					_cmd = 65 + int(_speed * _factor)
				else:
					_cmd = self._CMD_MOTOR_A_STOP
					
		if (_motorID == self._MOTOR_B_ID):
			if (_speed == 0):
				_cmd = self._CMD_MOTOR_B_STOP
			else:
				if (_direction == self._REVERSE): #Range between 128-191
					_factor = (self._CMD_MOTOR_B_STOP - 1 - self._CMD_MOTOR_B_FULL_REVERSE) / 100.0
					_cmd = self._CMD_MOTOR_B_STOP - 1 - int(_speed * _factor)
				elif (_direction == self._FORWARD): #Range between 193-255
					_factor = (self._CMD_MOTOR_B_FULL_FORWARD - self._CMD_MOTOR_B_STOP - 1) / 100.0
					_cmd = 193 + int(_speed * _factor)
				else:
					_cmd = self._CMD_MOTOR_B_STOP
		
		#print ("Motor " + str(_motorID) + "   Direction: " + str(_direction) + "   Speed: " + str(_speed) + "   Factor = " + str(_factor) + "   CMD: " + str(_cmd))
		self.sp.write(chr(_cmd))
		
	def driveForward(self, _speed):
		self.driveMotor(self._MOTOR_A_ID, self._FORWARD, _speed)
		self.driveMotor(self._MOTOR_B_ID, self._FORWARD, _speed)

	def driveBackwards(self, _speed):
		self.driveMotor(self._MOTOR_A_ID, self._REVERSE, _speed)
		self.driveMotor(self._MOTOR_B_ID,self._REVERSE, _speed)
	
	def driveLeft(self, _speed):
		self.driveMotor(self._MOTOR_A_ID, self._REVERSE, _speed)
		self.driveMotor(self._MOTOR_B_ID, self._FORWARD, _speed)
	
	def driveRight(self, _speed):
		self.driveMotor(self._MOTOR_A_ID, self._FORWARD, _speed)
		self.driveMotor(self._MOTOR_B_ID, self._REVERSE, _speed)
	
class sabertooth:
	DEFAULT_ACCEL = 10
	DEFAULT_SPEED = 30
	
	def __init__(self, _port='/dev/ttyUSB0'):
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