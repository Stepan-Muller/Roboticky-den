import serial
import time

i = 1
while True:
	try:
		ser = serial.Serial('/dev/ttyACM0', 115200)
	except:
		print("Connection failed! Retrying... (", i, ")")
		i = i + 1
		continue
	break

def send_serial(state: bool, speedL: int, speedR: int, pickedColor: bool, resetCount: bool, dump: bool):
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
	
	ser.flushInput()
	
	return state, redCount, blueCount
