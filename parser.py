import serial
import time

while True:
	try:
		ser = serial.Serial('/dev/ttyACM0', 115200)
	except:
		continue
	break

def send_serial(state: bool, speedL: int, speedR: int, pickedColor: bool, resetCount: bool, dump: bool):
	ser.flushInput()
	ser.write(bytes([state, 100 + speedL, 100 + speedR, pickedColor, resetCount, dump, 255]))

def read_serial():
	data = []
	
	while True:
		byte = ser.read()
		
		if byte == bytes([255]) and len(data) > 7:
			break
			
		data.append(byte)
	
	state = data[0] != bytes([0])
	redCount = ord(data[1])
	blueCount = ord(data[2])
	
	print(ord(data[0]), ord(data[1]), ord(data[2]), ord(data[3]), ord(data[4]), ord(data[5]), ord(data[6]))
	
	return state, redCount, blueCount
