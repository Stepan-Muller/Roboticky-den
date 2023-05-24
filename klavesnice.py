import pid
import parser

import cv2
from picamera2 import Picamera2
import numpy as np
import time

speed = 50

width = 320
height = 240

picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

while True:	
	print(parser.read_serial())
	
	# Vzit obraz z kamery
	frame = picam2.capture_array()
	
	# Oprava barvy kamery (BGR na RGB)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
	cv2.imshow("Frame", frame)
	
	key = cv2.waitKey(1)
	
	if key == ord('q'):
		break
	elif key == ord('w'):
		parser.send_serial(True, speed, speed, False, False, False)
	elif key == ord('s'):
		parser.send_serial(True, -speed, -speed, False, False, False)
	elif key == ord('a'):
		parser.send_serial(True, -speed, speed, False, False, False)
	elif key == ord('d'):
		parser.send_serial(True, speed, -speed, False, False, False)
	else:
		parser.send_serial(True, 0, 0, False, False, False)
		
	time.sleep(0.1)
	
parser.send_serial(False, 0, 0, False, False, False)
