#! /usr/bin/python
#
import cv

dims = (1280, 720) # webcam dimensions

cap = cv.CreateCameraCapture(0)
cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH, dims[0])
cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT, dims[1])

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

