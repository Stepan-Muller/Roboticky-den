import pid
import parser

import cv2
from picamera2 import Picamera2
import numpy as np
import time
import statistics

# Cervena do fialova
lower_red_1 = np.array([120, 70, 90])
upper_red_1 = np.array([180, 255, 255])

# Cervena do oranzova
lower_red_2 = np.array([0, 90, 90])
upper_red_2 = np.array([10, 255, 255])

lower_blue = np.array([90, 90, 90])
upper_blue = np.array([110, 255, 255])

highlight_red_pucks = ([0, 0, 255])
highlight_red_home = ([0, 0, 100])

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

time_to_return = 0
start_time = time.time()

dump_pucks = False

# True = modrá, False = červená
home_color = False

picam2 = Picamera2()
picam2.preview_configuration.main.size = (width, height)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()

def go(seconds, left_speed, right_speed):
	move_start_time = time.time()
	
	while time.time() < move_start_time + seconds:
		parser.send_serial(True, left_speed, right_speed, home_color, False, dump_pucks)
		
		time.sleep(0.1)

def get_color_mask(frame, lower_color, upper_color):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
	
	mask = cv2.inRange(hsv, lower_color, upper_color)
	
	kernel = np.ones((5,5),np.uint8)
	mask = cv2.erode(mask, kernel, iterations=1)
	mask = cv2.dilate(mask, kernel, iterations=1)
	
	return mask

def is_above_white(frame, contour):
	x,y,w,h = cv2.boundingRect(contour)
	
	for i in range(y + h + 3, height - 15):
		color = frame[i, int(x + w / 2)]
		if int(color[0]) + int(color[1]) + int(color[2]) < 100 * 3:
			frame[i, int(x + w / 2)] = (0, 0, 0)
			return False
			
		frame[i, int(x + w / 2)] = (255, 255, 255)
			
	return True

def send_ray_to_wall(frame, x_offset):
	for i in range(0, height - 15):
		y = height - 15 - i
		
		color = frame[y, int(width / 2 + x_offset)]
	
		if int(color[0]) + int(color[1]) + int(color[2]) < 100 * 3:
			frame[y, int(width / 2 + x_offset)] = (0, 0, 0)
			dist_x, dist_y = get_coords_from_camera(width / 2, y)
			return dist_x
		
		frame[y, int(width / 2 + x_offset)] = (255, 255, 255)
	
	return float("inf")

def get_dist_from_wall(frame):
	rays = []
	
	for i in range(3):
		rays.append(send_ray_to_wall(frame, i * 50 - 50))
		
	return statistics.median(rays)

def get_contours_on_mat(frame, contours):
	correct_contours = []
	
	for contour in contours:
		if is_above_white(frame, contour):
			correct_contours.append(contour)
	
	return correct_contours	

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

	error = width / 2 - target
	
	if abs(error) < 25:
		error = 0

	pid.pid_motor(error)

going_home = False

last_y = float("inf")

target_x = 0
target_y = 0

updates_to_disable = 0

last_wall_time = 0
while True:	
	enabled, red_count, blue_count = parser.read_serial()
	
	print("Serial:		", enabled, red_count, blue_count)
	
	if enabled:
		updates_to_disable = 10
	else:
		updates_to_disable = updates_to_disable - 1
		
	if updates_to_disable <= 0:
		start_time = time.time()
	
	print("Time to return:	", int(start_time + time_to_return - time.time() + 0.1))
	
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
	
	# Hledat puky a domecek pouze nad platnem - bilou
	blue_contours = get_contours_on_mat(frame, blue_contours)
	red_contours = get_contours_on_mat(frame, red_contours)
	
	# Najit pouze puky o spravne velikosti
	blue_pucks = get_contours_of_area(blue_contours, 2, 5)
	red_pucks = get_contours_of_area(red_contours, 2, 5)
	
	# Najit domecky v obraze
	blue_home = get_biggest_contour(blue_contours, 5)
	red_home = get_biggest_contour(red_contours, 5)
	
	# Vykreslit puky a domecky
	highlight_contours(blue_pucks, highlight_blue_pucks)
	highlight_contours(red_pucks, highlight_red_pucks)
	
	if not blue_home == []:
		highlight_contours([blue_home], highlight_blue_home)
	if not red_home == []:
		highlight_contours([red_home], highlight_red_home)
	
	if home_color:
		target_home = blue_home
	else:
		target_home = red_home
	
	pucks = blue_pucks + red_pucks

	if start_time + 3 < time.time():
		if time.time() < start_time + time_to_return and red_count < 10 and blue_count < 10:
			if len(pucks) > 0:
				target, target_x, target_y = find_at_coords(pucks, target_x, target_y)
				track(target)
			
				# Pokud puk zajel pod robota, jet chvili rovne
				x,y,w,h = cv2.boundingRect(target)
				
				if last_y == height and not y + h == height:
					print("puk")
					go(0.5, 70, 70)
				
				last_y = y + h
			else:
				parser.send_serial(True, 30, -30, home_color, False, dump_pucks)
		elif time.time() >= start_time + time_to_return or red_count >= 10 or blue_count >= 10:
			if not target_home == []:
				track(target_home)
				
				# Pokud vjel robot nad domecek, otocit se, vypustit puky a zastavit
				x,y,w,h = cv2.boundingRect(target_home)
				
				if y + h >= height - 20:
					print("domecek")
					go(1.2, 70, 70)
					go(1.5, 70, -70)
					dump_pucks = True
					go(1.7, 70, 70)
					break
			else:
				wall_dist = get_dist_from_wall(frame)
				
				if wall_dist < 40:
					last_wall_time = time.time()
					parser.send_serial(True, -20, 40, home_color, False, dump_pucks)
				elif wall_dist < 50:
					last_wall_time = time.time()
				else:
					if last_wall_time + 0.7 > time.time():
						parser.send_serial(True, 0, 40, home_color, False, dump_pucks)
					else:
						parser.send_serial(True, 40, 40, home_color, False, dump_pucks)
	else:
		parser.send_serial(True, 0, 0, home_color, False, dump_pucks)
	
	cv2.imshow("Frame", frame)
	
	if cv2.waitKey(1) == ord('q'):
		break
		
	time.sleep(0.1)
	
parser.send_serial(False, 0, 0, home_color, False, dump_pucks)
