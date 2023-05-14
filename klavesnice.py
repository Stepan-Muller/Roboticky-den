import pygame
import parser

pygame.init()

size = [500, 500]
screen = pygame.display.set_mode(size)

pygame.display.set_caption("test")

font = pygame.font.SysFont(None, 25)

clock = pygame.time.Clock()

speed = 50

running = True
pressed = False
while running:
	pygame.event.pump()
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
	
	keys = pygame.key.get_pressed()

	parser.read_serial()

	if keys[pygame.K_a]:
		parser.send_serial(True, -speed, speed, False, False, False)
	elif keys[pygame.K_d]:
		parser.send_serial(True, speed, -speed, False, False, False)
	elif keys[pygame.K_s]:
		parser.send_serial(True, -speed, -speed, False, False, False)
	elif keys[pygame.K_w]:
		parser.send_serial(True, speed, speed, False, False, False)
	else:
		parser.send_serial(True, 0, 0, False, False, False)
	
	clock.tick(50)
	
pygame.quit()
