#!/usr/bin/python
#
# sudo apt-get install python-pygame
#
import pygame.camera
import pygame.image

pygame.camera.init()
# select camera last in the list. Highest number?
camera_dev = pygame.camera.list_cameras()[-1]
cam = pygame.camera.Camera(camera_dev)
cam.start()
img = cam.get_image()
pygame.image.save(img, "photo.png")
pygame.camera.quit()
