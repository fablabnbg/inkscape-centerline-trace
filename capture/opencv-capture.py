#! /usr/bin/python
#
# References:
# for cv2, cv3 see http://stackoverflow.com/questions/18458422/query-maximum-resolution-in-opencv
# 		http://stackoverflow.com/questions/7322939/how-to-count-cameras-in-opencv-2-3
# http://docs.opencv.org/modules/core/doc/drawing_functions.html
# http://docs.opencv.org/modules/core/doc/operations_on_arrays.html?highlight=avg#mean
#
import os
import cv

prop = {
  'bright':     [cv.CV_CAP_PROP_BRIGHTNESS],
  'contr':      [cv.CV_CAP_PROP_CONTRAST],
  'rgb':        [cv.CV_CAP_PROP_CONVERT_RGB],
  'expose':     [cv.CV_CAP_PROP_EXPOSURE],
  'format':     [cv.CV_CAP_PROP_FORMAT],
  'fourcc':     [cv.CV_CAP_PROP_FOURCC],
  'fps':        [cv.CV_CAP_PROP_FPS],
  'count':      [cv.CV_CAP_PROP_FRAME_COUNT],
  'height':     [cv.CV_CAP_PROP_FRAME_HEIGHT],
  'width':      [cv.CV_CAP_PROP_FRAME_WIDTH],
  'gain':       [cv.CV_CAP_PROP_GAIN],
  'hue':        [cv.CV_CAP_PROP_HUE],
  'mode':       [cv.CV_CAP_PROP_MODE],
  'rect':       [cv.CV_CAP_PROP_RECTIFICATION],
  'sat':        [cv.CV_CAP_PROP_SATURATION]
  }


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

gui = { 'prop': {}, 'step': 8, 'nav': 'm' }

idx = 0
for p in prop:
  x = cv.GetCaptureProperty(cap, prop[p][0])
  if x >= 0:
    idx += 1
    prop[p].append(idx)        # property exists
    prop[p].append(x)           # current value
    prop[p].append(x)           # initial value
  else:
    prop[p].append(0)

for p in prop:
  if prop[p][1]:
    print "property %s = '%s'" % (p, prop[p][2])
gui['prop'] = prop;

def draw_gui(cv, img):
  if not 'w' in gui: gui['w'] = img.width
  if not 'h' in gui: gui['h'] = img.height
  if not 'frame' in gui:
    frame = {
      'w': int(img.width /2+.5),
      'h': int(img.height/2+.5),
      'x': int(img.width /4+.5),
      'y': int(img.height/4+.5),
      'c':(255,0,255)
    }
    gui['frame'] = frame
  f = gui['frame']
  ww=int(f['w']/8+.5)
  hh=int(f['h']/8+.5)
  col=f['c']

  cv.Line(img, (f['x'],f['y']       ), (f['x']+ww,f['y']       ), col, 1)
  cv.Line(img, (f['x'],f['y']       ), (f['x']   ,f['y']+hh    ), col, 1)

  cv.Line(img, (f['x'],f['y']+f['h']), (f['x']+ww,f['y']+f['h']       ), col, 1)
  cv.Line(img, (f['x'],f['y']+f['h']), (f['x']   ,f['y']+f['h']-hh    ), col, 1)

  cv.Line(img, (f['x']+f['w'],f['y']+f['h']), (f['x']+f['w']-ww,f['y']+f['h']   ), col, 1)
  cv.Line(img, (f['x']+f['w'],f['y']+f['h']), (f['x']+f['w']   ,f['y']+f['h']-hh), col, 1)

  cv.Line(img, (f['x']+f['w'],f['y']), (f['x']+f['w']-ww,f['y']   ), col, 1)
  cv.Line(img, (f['x']+f['w'],f['y']), (f['x']+f['w']   ,f['y']+hh), col, 1)

def move_frame(dir):
  f = gui['frame']
  if dir == 1:
    # left
    f['x'] -= gui['step']
    if f['x'] <= 0: f['x'] = 0
  elif dir == 2:
    # up
    f['y'] -= gui['step']
    if f['y'] <= 0: f['y'] = 0
  elif dir == 3:
    # right
    f['x'] += gui['step']
    if f['x']+f['w'] >= gui['w']: f['x'] = gui['w'] - f['w']
  elif dir == 4:
    # down
    f['y'] += gui['step']
    if f['y']+f['h'] >= gui['h']: f['y'] = gui['h'] - f['h']
  else:
    pass

def scale_frame(dir):
  f = gui['frame']
  if dir == 1:
    # left
    f['w'] -= gui['step']
    if f['w'] <= gui['step']: f['w'] = gui['step']
  elif dir == 2:
    # up
    f['h'] -= gui['step']
    if f['h'] <= gui['step']: f['h'] = gui['step']
  elif dir == 3:
    # right
    f['w'] += gui['step']
    if f['x']+f['w'] >= gui['w']: f['w'] = gui['w'] - f['x']
  elif dir == 4:
    # down
    f['h'] += gui['step']
    if f['y']+f['h'] >= gui['h']: f['h'] = gui['h'] - f['y']
  else:
    pass


dropcount=0
state=0
while (True):
  img = cv.QueryFrame(cap)
  if img is None:
    break
  dropcount += 1
  if (dropcount >= 2):
    dropcount = 0
  if (dropcount >= 1):
    # drop every third image, so that we stay clear of 100% cpu consumption
    # and keep the v4l buffers drained at low water. This counters excess latency.
    continue

  gray = cv.CreateImage( (img.width, img.height), cv.IPL_DEPTH_8U, 1 );
  cv.CvtColor(img, gray, cv.CV_BGR2GRAY)
  # cv.Canny(gray, gray, 50, 150, 3)	# Canny edge detector does double lines.
  img = gray	# FIXME: expand to RGB again, so that we can draw a colorful GUI
  draw_gui(cv, img)

  cv.ShowImage('Camera Image', img)
  key_raw = cv.WaitKey(1)
  key = key_raw & 0xff    # force into ascii range

  # 65364 84 = c_down
  # 65362 82 = c_up
  # 65361 81 = c_left
  # 65363 83 = c_right
  # 65513 233 = alt
  # 65505 225 = shift

  if (chr(key) == 'h'): key_raw = 65361
  if (chr(key) == 'j'): key_raw = 65364
  if (chr(key) == 'k'): key_raw = 65362
  if (chr(key) == 'l'): key_raw = 65363

  if key_raw in (65364, 65362, 65361, 65363):
    if (gui['nav'] == 'm'):
      move_frame(key_raw-65360)
    else:
      scale_frame(key_raw-65360)
  elif key in ( 27, ord('q'), ord('Q'), ):
    break
  elif key in ( ord(' '), ord('w'), ord('W'), ):
    state = 1
  elif (chr(key) in "mrs"):
    gui['nav'] = chr(key)


  if state == 1:
    # convert to grayscale
    cv.SaveImage('pic.png', img)
    print("saving pic.png")
    state = 2
  elif state == 2:
    # fork autotrace
    pass
