import serial
import time

while True:
	try:
		ser = serial.Serial('/dev/ttyACM0', 115200)
	except:
		continue
	break

def send_serial(state: bool, speedL: int, speedR: int, pickedColor: bool, resetCount: bool, dump: bool):
	ser.write(bytes([state, speedL, speedR, pickedColor, resetCount, dump]))
	
	ser.write(bytes([255]))

def read_serial():
	data = []
	
	while True:
		byte = ser.read()
		
		if byte == bytes([255]) and len(data) > 2:
			break
			
		data.append(byte)
	
	state = data[0] != bytes([0])
	redCount = ord(data[1])
	blueCount = ord(data[2])
	
	return state, redCount, blueCount
