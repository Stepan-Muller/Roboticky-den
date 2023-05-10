import pid

import cv2
from picamera2 import Picamera2
import numpy as np

lower_green = np.array([10, 60, 0])
upper_green = np.array([90, 255, 255])

# Cervena do fialova
lower_red_1 = np.array([130, 90, 0])
upper_red_1 = np.array([180, 255, 255])
highlight_red_1 = ([255, 0, 255])

# Cervena do oranzova
lower_red_2 = np.array([0, 90, 0])
upper_red_2 = np.array([30, 255, 255])
highlight_red_2 = ([0, 0, 255])

lower_blue = np.array([80, 150, 0])
upper_blue = np.array([130, 255, 255])
highlight_blue = ([255, 0, 0])

width = 320
height = 240

camera_angle = 80
camera_fov_horizontal = 66
camera_fov_vertical = 37
camera_height = 10

picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

def get_contours(frame, lower_color, upper_color, highlight_color):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	mask = cv2.inRange(hsv, lower_color, upper_color)
	
	kernel = np.ones((5,5),np.uint8)
	mask = cv2.erode(mask, kernel, iterations=1)
	mask = cv2.dilate(mask, kernel, iterations=1)
	
	contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	
	big_contours = []
	
	for cnt in contours:
		area = cv2.contourArea(cnt)
		if area > 100: # Only consider contours with a certain area threshold
			x,y,w,h = cv2.boundingRect(cnt)
			cv2.rectangle(frame, (x, y), (x+w, y+h), highlight_color, 2)
			big_contours.append(cnt)
			
	return big_contours

def findClosest(contours):
	min_sqr_dist = 1E9
	
	for cnt in contours:
		x,y,w,h = cv2.boundingRect(cnt)
		angle_y = ((y + h) / -height + 0.5) * camera_fov_vertical + camera_angle
		dist_y = camera_height * abs(np.tan(np.deg2rad(angle_y)))
		angle_x = ((x + w) / -width + 0.5) * camera_fov_horizontal
		dist_x = camera_height * abs(np.tan(np.deg2rad(angle_x)))
		
		sqr_dist = pow(dist_y, 2) + pow(dist_x, 2)
		
		if sqr_dist < min_sqr_dist:
			min_sqr_dist = sqr_dist
			closest = cnt
			
	return closest, np.sqrt(min_sqr_dist)

while True:
	frame = picam2.capture_array()
	
	# Oprava barvy kamery (BGR na RGB)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
	contours = get_contours(frame, lower_green, upper_green, highlight_red_1)
	
	if len(contours) > 0:
		closest, distance = findClosest(contours)
		
		x,y,w,h = cv2.boundingRect(closest)
		cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
		target = int(x + w / 2)
		cv2.line(frame, (target, 0), (target, 480), (255, 0, 0), 2)
		error = width / 2 - target
		
		if abs(error) < 20:
			error = 0
		
		pid.pid_motor(error)
	
	cv2.line(frame, (int(width / 2), 0), (int(width / 2), height), (255, 0, 255), 2)
	
	cv2.imshow("Frame", frame)
	if cv2.waitKey(1) == ord('q'):
		break
