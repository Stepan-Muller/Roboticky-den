import pid
import parser

import cv2
from picamera2 import Picamera2
import numpy as np
import time

# Cervena do fialova
lower_red_1 = np.array([120, 70, 90])
upper_red_1 = np.array([180, 255, 255])

# Cervena do oranzova
lower_red_2 = np.array([0, 70, 90])
upper_red_2 = np.array([10, 255, 255])

highlight_red_pucks = ([0, 0, 255])
highlight_red_home = ([0, 0, 100])

lower_blue = np.array([95, 150, 90])
upper_blue = np.array([110, 255, 255])

highlight_blue_pucks = ([255, 0, 0])
highlight_blue_home = ([100, 0, 0])

width = 320
height = 240

camera_angle = 55
camera_fov_horizontal = 60
camera_fov_vertical = 45

camera_height = 29.5
camera_x_offset = 0
camera_y_offset = 0

time_to_return = float("inf") + time.time()
home_color = "red"

picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

def go_straight_seconds(seconds):
	start_time = time.time()
	
	while time.time() < start_time + seconds:
		parser.send_serial(True, 70, 70, False, False, False)
		
		time.sleep(0.1)

def get_color_mask(frame, lower_color, upper_color):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	mask = cv2.inRange(hsv, lower_color, upper_color)
	
	kernel = np.ones((5,5),np.uint8)
	mask = cv2.erode(mask, kernel, iterations=1)
	mask = cv2.dilate(mask, kernel, iterations=1)
	
	return mask

def get_distance_from_camera(x, y):
	angle_vertical = (y / -height + 0.5) * camera_fov_vertical + camera_angle
	angle_horizontal = (x / -width + 0.5) * camera_fov_horizontal
	
	dist_x = camera_height / np.cos(np.deg2rad(angle_vertical)) + camera_x_offset
	dist = dist_x / np.cos(np.deg2rad(angle_horizontal)) + camera_y_offset
	
	return dist

def get_contour_area(contour):
	vertical, horizontal, w, h = cv2.boundingRect(contour)
	dist = get_distance_from_camera(vertical + w / 2, horizontal + h)
	
	area = cv2.contourArea(contour)
	
	adj_area = np.tan(np.deg2rad(np.sqrt(area) / width * camera_fov_horizontal)) * dist
	
	return adj_area

def get_contours_of_area(contours, min_area, max_area):
	correct_contours = []
	
	for contour in contours:
		area = get_contour_area(contour)
		
		if area > min_area and area < max_area:
			correct_contours.append(contour)
	
	return correct_contours

def get_biggest_contour(contours, min_area):
	biggest = []
	
	for contour in contours:
		area = get_contour_area(contour)
		
		if area > min_area:
			biggest = contour
			min_area = area
			
	return biggest

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
		x, y = get_coords_from_camera(vertical + w / 2, horizontal + h)
		
		sqr_dist = pow(x - x_goal, 2) + pow(y - y_goal, 2)
		
		if sqr_dist < min_sqr_dist:
			min_sqr_dist = sqr_dist
			closest = contour
			closest_x = x
			closest_y = y
			
	return closest, closest_x, closest_y

def track(target):
	x,y,w,h = cv2.boundingRect(target)
	
	cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
	target = int(x + w / 2)
	
	# Nakreslit caru smeru puku (cil)
	cv2.line(frame, (target, 0), (target, 480), (0, 0, 255), 2)
	error = width / 2 - target
	
	if abs(error) < 20:
		error = 0

	pid.pid_motor(error)

going_home = False

last_y = float("inf")

target_x = 0
target_y = 0
while True:	
	print(parser.read_serial())
	
	# Vzit obraz z kamery
	frame = picam2.capture_array()
	
	# Oprava barvy kamery (BGR na RGB)
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
	# Najit barvu v obraze
	blue_mask = get_color_mask(frame, lower_blue, upper_blue)
	
	red_1_mask = get_color_mask(frame, lower_red_1, upper_red_1)
	red_2_mask = get_color_mask(frame, lower_red_2, upper_red_2)
	
	# Sloučit dve cervene masky
	red_mask = cv2.bitwise_or(red_1_mask, red_2_mask)
	
	# Najit puky v obraze
	blue_contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	red_contours, hierarchy = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	
	# Najit pouze puky o spravne velikosti
	blue_pucks = get_contours_of_area(blue_contours, 2, 5)
	red_pucks = get_contours_of_area(red_contours, 2, 5)
	
	# Najit domecky v obraze
	blue_home = get_biggest_contour(blue_contours, 10)
	red_home = get_biggest_contour(red_contours, 10)
	
	# Vykreslit puky a domecky
	highlight_contours(blue_pucks, highlight_blue_pucks)
	highlight_contours(red_pucks, highlight_red_pucks)
	
	if not blue_home == []:
		highlight_contours([blue_home], highlight_blue_home)
	if not red_home == []:
		highlight_contours([red_home], highlight_red_home)
	
	if home_color == "blue":
		target_home = blue_home
	elif home_color == "red":
		target_home = red_home
	else:
		target_home = []
	
	pucks = blue_pucks + red_pucks

	if time.time() < time_to_return and len(pucks) > 0:
		target, target_x, target_y = find_at_coords(pucks, target_x, target_y)
		track(target)
		
		x,y,w,h = cv2.boundingRect(target)
		
		if last_y == height and not y + h == height:
			print("konec")
			go_straight_seconds(0.5)
			
		last_y = y + h
	elif time.time() >= time_to_return and not target_home == []:
		track(target_home)
	else:
		parser.send_serial(True, 40, -40, False, False, False)
	
	# Nakreslit stredovou caru (cil)
	cv2.line(frame, (int(width / 2), 0), (int(width / 2), height), (0, 255, 0), 2)
	
	cv2.imshow("Frame", frame)
	
	if cv2.waitKey(1) == ord('q'):
		break
		
	time.sleep(0.1)
	
parser.send_serial(False, 0, 0, False, False, False)
