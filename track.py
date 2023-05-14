import pid
import parser

import cv2
from picamera2 import Picamera2
import numpy as np
import time

lower_green = np.array([10, 90, 70])
upper_green = np.array([90, 255, 255])
highlight_green = ([0, 255, 0])

# Cervena do fialova
lower_red_1 = np.array([120, 90, 70])
upper_red_1 = np.array([180, 255, 255])
highlight_red_1 = ([255, 0, 255])

# Cervena do oranzova
lower_red_2 = np.array([0, 90, 70])
upper_red_2 = np.array([30, 255, 255])
highlight_red_2 = ([0, 0, 255])

lower_blue = np.array([80, 150, 70])
upper_blue = np.array([110, 255, 255])
highlight_blue = ([255, 0, 0])

width = 320
height = 240

camera_angle = 65
camera_fov_horizontal = 66
camera_fov_vertical = 37

camera_height = 29
camera_x_offset = 2
camera_y_offset = 0

picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

def go_straight_seconds(seconds):
	start_time = time.time()
	
	while time.time() < start_time + seconds:
		parser.send_serial(True, 100, 100, False, False, False)
		
		time.sleep(0.1)

def get_contours(frame, lower_color, upper_color):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	mask = cv2.inRange(hsv, lower_color, upper_color)
	
	kernel = np.ones((5,5),np.uint8)
	mask = cv2.erode(mask, kernel, iterations=1)
	mask = cv2.dilate(mask, kernel, iterations=1)
	
	contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	
	return contours

def get_contours_of_area(contours, min_area, max_area):
	correct_contours = []
	
	for contour in contours:
		area = cv2.contourArea(contour)
		if area > 50:
			correct_contours.append(contour)
	
	return correct_contours

def highlight_contours(contours, color):
	for contour in contours:
		vertical, horizontal, w, h = cv2.boundingRect(contour)
		cv2.rectangle(frame, (vertical, horizontal), (vertical + w, horizontal + h), color)

def get_coords_from_camera(x, y):
	angle_vertical = (y / -height + 0.5) * camera_fov_vertical + camera_angle
	dist_x = camera_height * abs(np.tan(np.deg2rad(angle_vertical))) + camera_x_offset
	angle_horizontal = (x / -width + 0.5) * camera_fov_horizontal
	dist_y = camera_height * abs(np.tan(np.deg2rad(angle_horizontal))) + camera_y_offset
	
	return dist_x, dist_y

def find_at_coords(contours, x_goal, y_goal):
	min_sqr_dist = float("inf")
	
	for contour in contours:
		vertical, horizontal, w, h = cv2.boundingRect(contour)
		x, y = get_coords_from_camera(vertical + w / 2, horizontal + h / 2)
		
		sqr_dist = pow(x - x_goal, 2) + pow(y - y_goal, 2)
		
		if sqr_dist < min_sqr_dist:
			min_sqr_dist = sqr_dist
			closest = contour
			closest_x = x
			closest_y = y
			
	return closest, closest_x, closest_y

locked_x = 0
locked_y = 0

last_y = float("inf")
while True:
	# Vzit obraz z kamery
	frame = picam2.capture_array()
	
	# Oprava barvy kamery (BGR na RGB)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
	# Najit puky v obraze
	green_contours = get_contours(frame, lower_green, upper_green)
	
	red_1_contours = get_contours(frame, lower_red_1, upper_red_1)
	red_2_contours = get_contours(frame, lower_red_2, upper_red_2)
	
	# Najit pouze puky o spravne velikosti
	green_pucks = get_contours_of_area(green_contours, 30, 1000)

	red_1_pucks = get_contours_of_area(red_1_contours, 30, 1000)
	red_2_pucks = get_contours_of_area(red_2_contours, 30, 1000)
	
	# Vykreslit puky
	highlight_contours(green_pucks, highlight_green)

	highlight_contours(red_1_pucks, highlight_red_1)
	highlight_contours(red_2_pucks, highlight_red_2)
	
	pucks = green_pucks + red_1_pucks + red_2_pucks

	if len(pucks) > 0:
		target, locked_x, locked_y = find_at_coords(pucks, locked_x, locked_y)
		
		x,y,w,h = cv2.boundingRect(target)
		
		if last_y == height and not y + h == height:
			print("konec")
			go_straight_seconds(0.5)
		
		last_y = y + h
		
		cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
		target = int(x + w / 2)
		
		# Nakreslit caru smeru puku (cil)
		cv2.line(frame, (target, 0), (target, 480), (0, 0, 255), 2)
		error = width / 2 - target
		
		if abs(error) < 20:
			error = 0
		
		pid.pid_motor(error)
	else:
		parser.send_serial(True, -70, 70, False, False, False)
	
	# Nakreslit stredovou caru (cil)
	cv2.line(frame, (int(width / 2), 0), (int(width / 2), height), (0, 255, 0), 2)
	
	cv2.imshow("Frame", frame)
	
	if cv2.waitKey(1) == ord('q'):
		break
		
	time.sleep(0.1)
	

