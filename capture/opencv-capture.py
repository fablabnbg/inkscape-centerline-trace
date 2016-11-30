#! /usr/bin/python
#
# for cv2, cv3 see also http://stackoverflow.com/questions/18458422/query-maximum-resolution-in-opencv
#
import os
import cv

camera_resolutions = (
  ( 4000, 3000 ),
  ( 1600, 1200 ),
  ( 1280, 960 ),
  ( 1024, 768 ),
  ( 960, 540 ),
  ( 800, 600 ),
  ( 640, 480 ),
  ( 320, 240 ),
)

# select camera with highest number, fallback to 0
camera_num = 10
while camera_num > 0:
  path= "/dev/video%s" % camera_num
  if os.path.exists(path):
    break
  camera_num = camera_num - 1

cap = cv.CreateCameraCapture(camera_num)

width_seen = 0
height_seen = 0
for dims in camera_resolutions:
  if dims[0] <= width_seen:
    print "successful resolution: %dx%d (width >= %d)" % (width_seen,heigth_seen, dims[0])
    break
  cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH, dims[0])
  cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT, dims[1])
  width_seen = cv.GetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH)
  heigth_seen = cv.GetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT)
  print "try %dx%d got %dx%d" % (dims[0], dims[1], width_seen, heigth_seen)

if not cap:
  print "Error opening WebCAM"
  sys.exit(1)

while 1:
  frame = cv.QueryFrame(cap)
  if frame is None:
    break
  cv.ShowImage('Camera Image', frame)
  if 0xFF & cv.WaitKey(1) in (27,ord('q'),ord('Q'),):
    break

