#! /usr/bin/python
#
# vectorize strokes in a graymap png file 
# as a path along the centerline of the strokes.
#
# This is done with autotrace -centerline, as
# the builtin potrace in inkscape cannot do centerline --
# it would always draw a path around the contour of the 
# stroke, resulting in double lines.
#
# We want a stroke represented by a single path (optionally with line-width) , 
# rather than its outline contour.
#
# Algorithm:
# autotrace needs a bi-level bitmap. In order to find the
# best threshold value, we run autotrace at multiple thresholds
# and evaluate the result.
#
# We count the number of line segments produced and 
# measure the total path length drawn.
#
# The svg that has the longest path but the least number of
# segments is returned.
#
# Requires: 
# apt-get install autotrace

import sys, os, re, math, tempfile, subprocess
import xml.etree.ElementTree as ET
from PIL import Image
from PIL import ImageOps
from PIL import ImageStat

num_attempts = 15	# min 1, max 255, beware it gets much slower with more attempts.
autotrace_cmd = ['autotrace', '--centerline', '--input-format=pbm', '--output-format=svg' ]
autotrace_cmd += sys.argv[2:]

stroke_style_add = 'stroke-width:%.2f; fill:none; stroke-linecap:round;'

im = Image.open(sys.argv[1]).convert(mode='L', dither=None)
# print [im.format, im.size, im.mode]
im = ImageOps.equalize(im)	# equalize histogram
#im.show()

def svg_pathstats(path_d):
  """ calculate statistics from an svg path:
      length (measuring bezier splines as straight lines through the handles).
      points (all, including duplicates)
      segments (number of not-connected!) path segments.
  """
  path_d = path_d.lower()
  p_points = 0
  p_length = 0
  p_segments = 0
  for p in path_d.split('m'):
    # print "xxxx",p

    pp = re.sub('[cl,]', ' ', p)
    pp,closed = re.subn('z\s*$','',pp)
    xy = pp.split()
    if len(xy) < 2:
      # print len(pp)
      # print "short path error"
      continue
    x0 = float(xy[0])
    y0 = float(xy[1])
    p_points += 1
    x = xy[2::2]
    y = xy[3::2]
    if len(x):
      p_segments += 1
      if closed:
        x.extend(x0)
        y.extend(y0)

    for i in range(len(x)):
      p_points += 1
      dx = float(x[i]) - x0
      dy = float(y[i]) - y0
      p_length += math.sqrt( dx * dx + dy * dy )
      x0,y0 = float(x[i]),float(y[i])

  return { 'points':p_points, 'segments':p_segments, 'length':p_length }

# slice with a list of histogram maps
# 1 -> 128
# 3 -> 64,128,192
# ...

candidate = {}

for i in range(num_attempts):
  threshold = int(256.*(1+i)/(num_attempts+1))
  lut = [ 255 for n in range(threshold) ] + [ 0 for n in range(threshold,256) ]
  bw = im.point(lut, mode='1')
  cand = { 'threshold':threshold, 'img_width':bw.size[0], 'img_height':bw.size[1], 'mean': ImageStat.Stat(im).mean[0] }
  fp = tempfile.NamedTemporaryFile(suffix='.pbm', delete=False)
  fp.write("P4\n%d %d\n" % (bw.size[0], bw.size[1]))
  fp.write(bw.tobytes())
  fp.close()
  try:
    p = subprocess.Popen(autotrace_cmd + [fp.name], stdout=subprocess.PIPE)
  except Exception as e:
    print '+ '+' '.join(autotrace_cmd)
    print e
    print "Try:\n  sudo apt-get install autotrace"
    sys.exit(1)

  cand['svg'] = p.communicate()[0]
  os.unlink(fp.name)
  # <?xml version="1.0" standalone="yes"?>\n<svg width="86" height="83">\n<path style="stroke:#000000; fill:none;" d="M36 15C37.9219 18.1496 41.7926 19.6686 43.2585 23.1042C47.9556 34.1128 39.524 32.0995 35.179 37.6034C32.6296 40.8328 34 48.1105 34 52M36 17C32.075 22.4565 31.8375 30.074 35 36M74 42L46 38C45.9991 46.1415 46.7299 56.0825 45.6319 64C44.1349 74.7955 23.7094 77.5566 16.044 72.3966C7.27363 66.4928 8.04426 45.0047 16.2276 38.7384C20.6362 35.3626 27.7809 36.0006 33 36M44 37L45 37"/>\n</svg>
  xml = ET.fromstring(cand['svg'])
  p_len,p_seg,p_pts = 0,0,0
  for p in xml.findall('path'):
    pstat = svg_pathstats(p.attrib['d'])
    p_len += pstat['length']
    p_seg += pstat['segments']
    p_pts += pstat['points']
  cand['length']   = p_len
  cand['segments'] = p_seg
  cand['points']   = p_pts
  
  if cand['mean'] > 127: 
    cand['mean'] = 255 - cand['mean']	# should not happen
  blackpixels = cand['img_width'] * cand['img_height'] * cand['mean'] / 255.
  cand['strokewidth'] = blackpixels / cand['length']
  candidate[i] = cand

def calc_weight(cand, idx):
  offset = (num_attempts/2.-idx) * (num_attempts/2.-idx) * (cand['img_width']+cand['img_height'])
  w = cand['length']*5 - offset*.005 - cand['points']*.2 - cand['segments']*20
  # print "calc_weight(%d) = rl=%f o=%f p=%f s=%f -> w=%f" % (idx, cand['length']*5, offset*.005, cand['points']*.2, cand['segments']*20, w)
  return w

best_weight_idx = 0
for n in candidate.keys():
  # print "candidate ", n
  c = candidate[n]
  # print "\t mean=%d len=%d seg=%d width=%d" % (c['mean'], c['length'], c['segments'], c['strokewidth'])
  if calc_weight(c,n) > calc_weight(candidate[best_weight_idx], best_weight_idx):
    best_weight_idx = n

print >>sys.stderr, "best: %d/%d" % (best_weight_idx, num_attempts)
svg = re.sub('stroke:', (stroke_style_add % candidate[best_weight_idx]['strokewidth']) + ' stroke:', candidate[best_weight_idx]['svg'])
print svg
