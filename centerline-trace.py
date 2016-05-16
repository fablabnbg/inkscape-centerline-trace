#!/usr/bin/env python
#
# Inkscape extension to vectorize bitmaps by tracing along the center of lines
# (C) 2016 juewei@fabmail.org
# Distribute under GPL-2.0 or ask.
#
# code snippets visited to learn the extension 'effect' interface:
# - convert2dashes.py
# - http://github.com/jnweiger/inkscape-silhouette
# - http://github.com/jnweiger/inkscape-gears-dev
# - http://sourceforge.net/projects/inkcut/
# - http://code.google.com/p/inkscape2tikz/
# - http://code.google.com/p/eggbotcode/
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
#
# The input image is converted to a graymap and histogram normalized with PIL.ImageOps.equalize. or autocontrast
#
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
# apt-get install autotrace python-pil
#
# 2016-05-10 jw, V0.1 -- initial draught
# 2016-05-11 jw, V0.2 -- first usable inkscape-extension
# 2016-05-15 jw, V0.3 -- equal spatial illumination applied. autocontrast instead of equalize. denoise.
#

__version__ = '0.3'	# Keep in sync with chain_paths.inx ca line 22
__author__ = 'Juergen Weigert <juewei@fabmail.org>'

import sys, os, re, math, tempfile, subprocess, base64

try:
  from PIL import Image
  from PIL import ImageOps
  from PIL import ImageStat
  from PIL import ImageFilter
except:
  print >>sys.stderr, "Error: Cannot import PIL. Try\n  apt-get install python-pil"
  sys.exit(1)


# debug = True
debug = False

# search path, so that inkscape libraries are found when we are standalone.
sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):	# windows
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
elif sys_platform.startswith('darwin'):	# mac
  sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
else:   				# linux
  # if sys_platform.startswith('linux'):
  sys.path.append('/usr/share/inkscape/extensions')

# inkscape libraries
import inkex, simplestyle
import cubicsuperpath

inkex.localize()

from optparse import SUPPRESS_HELP

def uutounit(self,nn,uu):
  try:
    return self.uutounit(nn,uu)		# inkscape 0.91
  except:
    return inkex.uutounit(nn,uu)	# inkscape 0.48

class TraceCenterline(inkex.Effect):
  """
  Inkscape Extension make long continuous paths from smaller parts
  """
  def __init__(self):
    # Call the base class constructor.
    inkex.Effect.__init__(self)

    self.dumpname= os.path.join(tempfile.gettempdir(), "trace-centerline.dump")
    self.autotrace_opts=[]		 # extra options for autotrace tuning.
    self.megapixel_limit = 2.0		 # max image size (limit needed, as we have no progress indicator)
    self.invert_image = False		 # True: trace bright lines.
    self.candidates = 15		 # [1..255] Number of autotrace candidate runs.
    self.filter_median = 0		 # 0 to disable median filter.
    self.filter_equal_light = 0.0        # [0.0 .. 1.9] Use 1.0 with photos. Use 0.0 with perfect scans.

    try:
      self.tty = open("/dev/tty", 'w')
    except:
      try:
        self.tty = open("CON:", 'w')	# windows. Does this work???
      except:
        self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
    if debug: print >>self.tty, "__init__"

    self.OptionParser.add_option('-V', '--version',
          action = 'store_const', const=True, dest='version', default=False,
          help='Just print version number ("'+__version__+'") and exit.')
    self.OptionParser.add_option('-i', '--invert', action='store', type='inkbool', default=False, help='Trace bright lines. (Default: dark lines)')
    self.OptionParser.add_option('-m', '--megapixels', action='store',
          type='float', default=2.0, help="Limit image size in megapixels. (Lower is faster)")
    self.OptionParser.add_option('-e', '--equal-light', action='store',
          type='float', default=0.0, help="Equalize illumination. Use 1.0 with flash photography, use 0.0 to disable.")
    self.OptionParser.add_option('-c', '--candidates', action='store',
          type='int', default=15, help="[1..255] Autotrace candidate runs. (Lower is much faster)")
    self.OptionParser.add_option('-d', '--despecle', action='store',
          type='int', default=0, help="[0..9] Apply median filter for noise reduction. (Default 0, off)")

  def version(self):
    return __version__
  def author(self):
    return __author__

  def svg_centerline_trace(self, image_file):
    """ svg_centerline_trace prepares the image by
    a) limiting_size (aka runtime), 
    b) removing noise, 
    c) linear histogram expansion, 
    d) equalized spatial illumnination (my own algorithm)

    Then we run several iterations of autotrace and find the optimal black white threshold by evaluating
    all outputs. The output with the longest total path and the least path elements wins.
    """
    num_attempts = self.candidates	# 15 is great. min 1, max 255, beware it gets much slower with more attempts.
    autotrace_cmd = ['autotrace', '--centerline', '--input-format=pbm', '--output-format=svg' ]
    autotrace_cmd += self.autotrace_opts

    stroke_style_add = 'stroke-width:%.2f; fill:none; stroke-linecap:round;'

    if debug: print >>sys.stderr, "svg_centerline_trace start "+image_file
    im = Image.open(image_file)
    im = im.convert(mode='L', dither=None)
    if debug: print >>sys.stderr, "seen: " + str([im.format, im.size, im.mode])
    scale_limit = math.sqrt(im.size[0] * im.size[1] * 0.000001 / self.megapixel_limit)
    if scale_limit > 1.0:
      print >>sys.stderr, "Megapixel limit ("+str(self.megapixel_limit)+ ") exceeded. Scaling down by factor : "+str(scale_limit)
      im = im.resize((int(im.size[0]/scale_limit), int(im.size[1]/scale_limit)), resample = Image.BILINEAR)

    if self.invert_image: im = ImageOps.invert(im)

    if self.filter_median > 0:
      if self.filter_median % 2 == 0: self.filter_median = self.filter_median + 1	# need odd values.
      im = im.filter(ImageFilter.MedianFilter(size=self.filter_median))	# a feeble denoise attempt. FIXME: try ROF instead.
    im = ImageOps.autocontrast(im, cutoff=2)	# linear expand histogram (an alternative to equalize)

    # not needed here:
    # im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))	# parameters depend on size of image!

    if self.filter_equal_light > 0.0:
      scale_thumb = math.sqrt(im.size[0] * im.size[1] * 0.0001) 	# exactly 0.01 MP (e.g. 100x100)
      im_neg_thumb = ImageOps.invert(im.resize((int(im.size[0]/scale_thumb), int(im.size[1]/scale_thumb)), resample = Image.BILINEAR))
      im_neg_thumb = im_neg_thumb.filter(ImageFilter.GaussianBlur(radius=30))
      im_neg_blur = im_neg_thumb.resize(im.size, resample=Image.BILINEAR)
      if debug: im_neg_blur.show()

      if debug: print >>sys.stderr, "ImageOps.equalize(im) done"
      im = Image.blend(im, im_neg_blur, self.filter_equal_light*0.5)
      im = ImageOps.autocontrast(im, cutoff=0)	# linear expand histogram (an alternative to equalize)
      if debug: im.show()

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
      if debug: print >>sys.stderr, "attempt "+ str(i)
      bw = im.point(lut, mode='1')
      if debug: print >>sys.stderr, "bw from lut done"
      cand = { 'threshold':threshold, 'img_width':bw.size[0], 'img_height':bw.size[1], 'mean': ImageStat.Stat(im).mean[0] }
      fp = tempfile.NamedTemporaryFile(suffix='.pbm', delete=False)
      fp.write("P4\n%d %d\n" % (bw.size[0], bw.size[1]))
      fp.write(bw.tobytes())
      fp.close()
      if debug: print >>sys.stderr, "pbm from bw done"
      try:
        p = subprocess.Popen(autotrace_cmd + [fp.name], stdout=subprocess.PIPE)
      except Exception as e:
        print '+ '+' '.join(autotrace_cmd)
        print e
        print "Try:\n  sudo apt-get install autotrace"
        sys.exit(1)

      cand['svg'] = p.communicate()[0]
      if debug: print >>sys.stderr, "autotrace done"

      os.unlink(fp.name)
      # <?xml version="1.0" standalone="yes"?>\n<svg width="86" height="83">\n<path style="stroke:#000000; fill:none;" d="M36 15C37.9219 18.1496 41.7926 19.6686 43.2585 23.1042C47.9556 34.1128 39.524 32.0995 35.179 37.6034C32.6296 40.8328 34 48.1105 34 52M36 17C32.075 22.4565 31.8375 30.074 35 36M74 42L46 38C45.9991 46.1415 46.7299 56.0825 45.6319 64C44.1349 74.7955 23.7094 77.5566 16.044 72.3966C7.27363 66.4928 8.04426 45.0047 16.2276 38.7384C20.6362 35.3626 27.7809 36.0006 33 36M44 37L45 37"/>\n</svg>
      xml = inkex.etree.fromstring(cand['svg'])
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
      cand['strokewidth'] = blackpixels / max(cand['length'],1.0)
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

    if debug: print >>sys.stderr, "best: %d/%d" % (best_weight_idx, num_attempts)
    ## if standalone:
    # svg = re.sub('stroke:', (stroke_style_add % candidate[best_weight_idx]['strokewidth']) + ' stroke:', candidate[best_weight_idx]['svg'])
    # return svg

    ## inkscape-extension:
    return ( candidate[best_weight_idx]['svg'], candidate[best_weight_idx]['strokewidth'], im.size )


  def calc_unit_factor(self, units='mm'):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        dialog_units = uutounit(self, 1.0, units)
        self.unit_factor = 1.0 / dialog_units
        return self.unit_factor

  def effect(self):
    if self.options.version:
      print __version__
      sys.exit(0)
    if self.options.megapixels  is not None: self.megapixel_limit    = self.options.megapixels
    if self.options.candidates  is not None: self.candidates         = self.options.candidates
    if self.options.invert      is not None: self.invert_image       = self.options.invert
    if self.options.despecle    is not None: self.filter_median      = self.options.despecle
    if self.options.equal_light is not None: self.filter_equal_light = self.options.equal_light

    self.calc_unit_factor()

    if not len(self.selected.items()):
      inkex.errormsg(_("Please select an image."))
      return

    for id, node in self.selected.iteritems():
      if debug: print >>self.tty, "id="+str(id), "tag="+str(node.tag)
      if node.tag != inkex.addNS('image','svg'):
        inkex.errormsg(_("Object "+id+" is not an image. seen:"+str(node.tag)+" expected:"+inkex.addNS('image','svg')+"\n Try - Object->Ungroup"))
        return
      # handle two cases. Embedded and linked images
      # <image .. xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAT8AA ..." preserveAspectRatio="none" height="432" width="425" transform="matrix(1,0,-0.52013328,0.85408511,0,0)"/>
      # <image  .. xlink:href="file:///home/jw/schaf.png"

      href=str(node.get(inkex.addNS('href','xlink')))

      # ######################
      #
      # dump the entire svg to file, so that we can examine what an image is.
      # f=open(self.dumpname, 'w')
      # f.write(href)
      # f.close()
      # if debug: print >>self.tty, "Dump written to "+self.dumpname
      #
      # ######################

      if href[:7] == 'file://':
        filename=href[7:]
        if debug: print >>self.tty, "linked image: ="+filename
      elif href[0] == '/' or href[0] == '.':
        filename=href
        if debug: print >>self.tty, "linked image path: ="+filename
      elif href[:15] == 'data:image/png;':
        if debug: print >>self.tty, "embedded image: "+href[:15+7]
        png=base64.decodestring(href[15+7:])
	f=tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
	f.write(png)
	filename=f.name
	f.close()
      else:
        inkex.errormsg(_("Neither file:// nor data:image/png; prefix. Cannot parse PNG image href "+href))
	sys.exit(1)
      if debug: print >>self.tty, "filename="+filename
      #
      path_svg,stroke_width,im_size = self.svg_centerline_trace(filename)
      xml = inkex.etree.fromstring(path_svg)
      path_d=xml.find('path').attrib['d']

      x_off = float(node.get('x'))
      y_off = float(node.get('y'))
      sx = float(node.get('width'))/im_size[0]
      sy = float(node.get('height'))/im_size[1]
      if debug: print >>self.tty, "im_width ", node.get('width'), "sx=",sx
      if debug: print >>self.tty, "im_height ", node.get('height'), "sy=",sy
      if debug: print >>self.tty, "im_x ", x_off
      if debug: print >>self.tty, "im_y ", y_off
      if debug: print >>self.tty, "pixel_size= ", im_size
      ## map the coordinates of the returned pixel path to the coordinates of the original SVG image.
      matrix = "translate(%g,%g) scale(%g,%g)" % (x_off, y_off, sx, sy)
      #
      if href[:5] == 'data:':
        os.unlink(filename) 		## it was a temporary file (representing an embedded image).
      #
      # Create SVG Path
      style = { 'stroke': '#000000', 'fill': 'none', 'stroke-linecap': 'round', 'stroke-width': stroke_width }
      if self.invert_image: style['stroke'] = '#777777'
      path_attr = { 'style': simplestyle.formatStyle(style), 'd': path_d, 'transform': matrix }
      ## insert the new path object
      inkex.etree.SubElement(self.current_layer, inkex.addNS('path', 'svg'), path_attr)



if __name__ == '__main__':
        e = TraceCenterline()

        e.affect()
        sys.exit(0)    # helps to keep the selection
