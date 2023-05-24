import parser

k_p = 0.5
k_i = 0
k_d = 0

max_i = 100
i = 0

last_error = 0

def pid(error):
	global k_p, k_i, k_d, max_i, i, last_error
	
	p = error * k_p
	i = i + error * k_i
	d = (last_error - error) * k_d
	
	i = max(-max_i, min(max_i, i))

	last_error = error
	
	PID = p
	
	return PID

target_speed = 70
max_speed = 90

def pid_motor(error):
	PID = pid(error)
	
	motor_l = int(max(min(target_speed - PID, max_speed), -max_speed))
	motor_r = int(max(min(target_speed + PID, max_speed), -max_speed))
	
	parser.send_serial(True, motor_l, motor_r, False, False, False)
