#!/usr/bin/env python3
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
# 2016-05-16 jw, V0.4 -- added replace option. Made filters optional.
# 2016-11-05 jw, V0.5 -- support embedded jpeg (and possibly other file types)
#			 https://github.com/fablabnbg/inkscape-centerline-trace/issues/8
# 2016-11-06 jw, V0.6 -- support transparent PNG images by applying white background
#			 https://github.com/fablabnbg/inkscape-centerline-trace/issues/3
# 2016-11-07 jw, V0.7 -- transparency: use black background when the '[x] trace white line' is enabled.
# 2017-03-05 jw,      -- instructions for mac added: http://macappstore.org/autotrace/
# 2017-07-12 jw,      -- instructions for windows added: https://inkscape.org/en/gallery/item/10567/centerline_NIH0Rhk.pdf
# 2018-06-20 jw,      -- usual suspects for paths to find autotrace on osx.
# 2018-08-10 jw, V0.7b --  require python-lxml for deb.
# 2018-08-31 jw, V0.8 -- MacOS instructions updated and MacOS path added for autotrace 0.40.0 from
#                        https://github.com/jnweiger/autotrace/releases
# 2018-09-01 jw, V0.8a -- Windows Path added
# 2018-09-03 jw, V0.8b -- New option: cliprect, hairline, at_filter_iterations, at_error_threshold added.
#                         Fixed stroke_width of scaled images.
# 2018-09-04 jw, V0.8c -- Fixed https://github.com/fablabnbg/inkscape-centerline-trace/issues/28
#                         Hints for https://github.com/fablabnbg/inkscape-centerline-trace/issues/27 added.
# 2019-03-24 jw, V0.8d -- Pad one pixel border to images, so that lines touching edges are recognized by autotrace.


__version__ = '0.8d'	# Keep in sync with centerline-trace.inx ca. line 3 and 24
__author__ = 'Juergen Weigert <juergen@fabmail.org>'

import sys, os, re, math, tempfile, subprocess, base64, time

try:
  from PIL import Image
  from PIL import ImageOps
  from PIL import ImageStat
  from PIL import ImageFilter
except:
  print >>sys.stderr, "Error: Cannot import PIL. Try\n  apt-get install python-pil"
  sys.exit(1)


debug = False
# debug = True

autotrace_exe = 'autotrace'

# search path, so that inkscape libraries are found when we are standalone.
sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):	# windows
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
  os.environ['PATH'] += os.pathsep + 'C:\Program Files\Inkscape\share\extensions'
  os.environ['PATH'] += os.pathsep + 'C:\Program Files (x86)\AutoTrace'
  os.environ['PATH'] += os.pathsep + 'C:\Program Files\AutoTrace'
elif sys_platform.startswith('darwin'):	# mac
  sys.path.append(       '/Applications/Inkscape.app/Contents/Resources/extensions')
  os.environ['PATH'] += ':/Applications/Inkscape.app/Contents/Resources/extensions'
  os.environ['PATH'] += ':' + os.environ.get('HOME', '') + '/.config/inkscape/extensions'
  os.environ['PATH'] += ':/Applications/autotrace.app/Contents/MacOS'
  os.environ['PATH'] += ':/usr/local/bin:/usr/local/lib'
else:   				# linux
  # if sys_platform.startswith('linux'):
  sys.path.append('/usr/share/inkscape/extensions')

# inkscape libraries
import inkex, simplestyle
import cubicsuperpath

try:
  # only since inkscape 0.91
  inkex.localize()
except:
  pass

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
    self.replace_image = False		 # True: remove image object when adding path object.
    self.candidates = 15		 # [1..255] Number of autotrace candidate runs.
    self.filter_median = 0		 # 0 to disable median filter.
    self.filter_equal_light = 0.0        # [0.0 .. 1.9] Use 1.0 with photos. Use 0.0 with perfect scans.
    self.hairline = False                # Fixed linewidth.
    self.hairline_width = 0.1            # Width of hairline [mm]

    # Test if autotrace is installed and in path
    command = autotrace_exe + ' --version'

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return_code = p.wait()

    out,err = p.communicate()

    found = out.find('AutoTrace')
    if found == -1:
        print >>sys.stderr, err
        if err.find('cannot open shared object file'):
          print >>sys.stderr, "NOTE: This build of autotrace is incompatible with your system, try a different build.\n"
        print >>sys.stderr, "You need to install autotrace for this extension to work. Try https://github.com/jnweiger/autotrace/releases or search for autotrace version 0.40.0 or later."
        exit()

    try:
      self.tty = open("/dev/tty", 'w')
    except:
      try:
        self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
      except:
        self.tty = open("CON:", 'w')	# windows. Does this work???
    if debug: print >>self.tty, "TraceCenterline: __init__"

    self.OptionParser.add_option('-V', '--version',
          action = 'store_const', const=True, dest='version', default=False,
          help='Just print version number ("'+__version__+'") and exit.')
    self.OptionParser.add_option('-i', '--invert', action='store', type='inkbool', default=False, help='Trace bright lines. (Default: dark lines)')
    self.OptionParser.add_option('-C', '--cliprect', action='store', type='inkbool', default=False, help='Clip to selected rectangle. (Default: Trace entire bitmap)')
    self.OptionParser.add_option('-r', '--remove', action='store', type='inkbool', default=False, help='Replace image with vector graphics. (Default: Place on top)')
    self.OptionParser.add_option('-H', '--hairline', action='store', type='inkbool', default=False, help='Fixed linewidth. (Default: Automatic)')
    self.OptionParser.add_option('-W', '--hairline-width', action='store',
          type='float', default=0.1, help="Width of a hairline [mm] (Default: 0.1)")

    self.OptionParser.add_option('--at-error-threshold', action='store',
          type='float', default=2.0, help="Autotrace: Subdivide fitted curves that are offset by a number of pixels exceeding the specified real number (default: 2.0)")
    self.OptionParser.add_option('--at-filter-iterations', action='store',
          type='int', default=4, help="Autotrace: Smooth the curve the specified number of times prior to fitting (default: 4)")

    self.OptionParser.add_option('-m', '--megapixels', action='store',
          type='float', default=2.0, help="Limit image size in megapixels. (Lower is faster)")
    self.OptionParser.add_option('-e', '--equal-light', action='store',
          type='float', default=0.0, help="Equalize illumination. Use 1.0 with flash photography, use 0.0 to disable.")
    self.OptionParser.add_option('-c', '--candidates', action='store',
          type='int', default=15, help="[1..255] Autotrace candidate runs. (Lower is much faster)")
    self.OptionParser.add_option('-d', '--despecle', action='store',
          type='int', default=0, help="[0..9] Apply median filter for noise reduction. (Default 0, off)")
    self.OptionParser.add_option('-D', '--debug-show', action='store_const', const=True, default=False, dest='debug', help='debugging: shows processed pictures.')

  def version(self):
    return __version__
  def author(self):
    return __author__

  def svg_centerline_trace(self, image_file, cliprect=None):
    """ svg_centerline_trace prepares the image by
    a) limiting_size (aka runtime),
    b) removing noise,
    c) linear histogram expansion,
    d) equalized spatial illumnination (my own algorithm)

    Then we run several iterations of autotrace and find the optimal black white threshold by evaluating
    all outputs. The output with the longest total path and the least path elements wins.

    A cliprect dict with the keys x, y, w, h can be specified. All 4 are expected in the
    range 0..1 and are mapped to the image width and height.
    """
    num_attempts = self.candidates	# 15 is great. min 1, max 255, beware it gets much slower with more attempts.
    autotrace_cmd = [ autotrace_exe,
        '--filter-iterations', str(self.options.at_filter_iterations),
        '--error-threshold', str(self.options.at_error_threshold),
        '--centerline',
        '--input-format=pbm',
        '--output-format=svg' ]
    autotrace_cmd += self.autotrace_opts

    stroke_style_add = 'stroke-width:%.2f; fill:none; stroke-linecap:round;'


    if debug: print >>self.tty, "svg_centerline_trace start "+image_file
    if debug: print >>self.tty, '+ '+' '.join(autotrace_cmd)
    im = Image.open(image_file)
    orig_im_size = (im.size[0], im.size[1])
    box=[0,0,0,0]
    if cliprect is not None:
      box[0] = cliprect['x'] * im.size[0]
      box[1] = cliprect['y'] * im.size[1]
      # sorted(min, val, max)[1] does clamping without chaining min(max()) in an ugly way.
      box[2] = sorted((0, int(0.5 + box[0] + cliprect['w'] * im.size[0]), im.size[0]))[1]
      box[3] = sorted((0, int(0.5 + box[1] + cliprect['h'] * im.size[1]), im.size[1]))[1]
      box[0] = sorted((0, int(0.5 + box[0]),                              im.size[0]))[1]
      box[1] = sorted((0, int(0.5 + box[1]),                              im.size[1]))[1]
      im = im.crop(box)
      if box[0] == box[2] or box[1] == box[3]:
        print >>sys.stderr, "ERROR: Cliprect and Image do not overlap.", orig_im_size, box, cliprect
        return ( '<svg/>', 1, orig_im_size)

    if 'A' in im.mode:
      # this image has alpha. Paste it onto white or black.
      im = im.convert("RGBA")
      if self.invert_image:
        bg = Image.new('RGBA', im.size, (0,0,0,255)) # black background
      else:
        bg = Image.new('RGBA', im.size, (255,255,255,255)) # white background
      im = Image.alpha_composite(bg, im)

    im = im.convert(mode='L', dither=None)
    if debug: print >>self.tty, "seen: " + str([im.format, im.size, im.mode])
    scale_limit = math.sqrt(im.size[0] * im.size[1] * 0.000001 / self.megapixel_limit)
    if scale_limit > 1.0:
      print >>sys.stderr, "Megapixel limit ("+str(self.megapixel_limit)+ ") exceeded. Scaling down by factor : "+str(scale_limit)
      im = im.resize((int(im.size[0]/scale_limit), int(im.size[1]/scale_limit)), resample = Image.BILINEAR)

    if self.invert_image: im = ImageOps.invert(im)

    ### Add a one pixel padding around the image. Otherwise autotrace fails when a line touches the edge of the image.
    im = ImageOps.expand(im, border=1, fill=255)

    if self.filter_median > 0:
      if self.filter_median % 2 == 0: self.filter_median = self.filter_median + 1	# need odd values.
      im = im.filter(ImageFilter.MedianFilter(size=self.filter_median))	                # feeble denoise attempt. FIXME: try ROF instead.
    im = ImageOps.autocontrast(im, cutoff=0)	# linear expand histogram (an alternative to equalize)
    ## cutoff=2 destroys some images, see https://github.com/fablabnbg/inkscape-centerline-trace/issues/28

    # not needed here:
    # im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))	# parameters depend on size of image!

    if self.filter_equal_light > 0.0:
      scale_thumb = math.sqrt(im.size[0] * im.size[1] * 0.0001) 	# exactly 0.01 MP (e.g. 100x100)
      im_neg_thumb = ImageOps.invert(im.resize((int(im.size[0]/scale_thumb), int(im.size[1]/scale_thumb)), resample = Image.BILINEAR))
      im_neg_thumb = im_neg_thumb.filter(ImageFilter.GaussianBlur(radius=30))
      im_neg_blur = im_neg_thumb.resize(im.size, resample=Image.BILINEAR)
      if self.options.debug: im_neg_blur.show()

      if debug: print >>self.tty, "ImageOps.equalize(im) done"
      im = Image.blend(im, im_neg_blur, self.filter_equal_light*0.5)
      im = ImageOps.autocontrast(im, cutoff=0)	# linear expand histogram (an alternative to equalize)
      if self.options.debug: im.show()

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
    if self.options.debug: im.show()

    for i in range(num_attempts):
      threshold = int(256.*(1+i)/(num_attempts+1))
      # make lookup table that maps to black/white using threshold.
      lut = [ 255 for n in range(threshold) ] + [ 0 for n in range(threshold,256) ]
      if debug: print >>self.tty, "attempt "+ str(i)
      bw = im.point(lut, mode='1')
      if debug: print >>self.tty, "bw from lut done: threshold=%d" % threshold
      if self.options.debug: bw.show(command="/usr/bin/display -title=bw:threshold=%d" % threshold)
      cand = { 'threshold':threshold, 'img_width':bw.size[0], 'img_height':bw.size[1], 'mean': ImageStat.Stat(im).mean[0] }
      fp = tempfile.NamedTemporaryFile(prefix="centerlinetrace", suffix='.pbm', delete=False)
      fp.write("P4\n%d %d\n" % (bw.size[0], bw.size[1]))
      fp.write(bw.tobytes())
      fp.close()
      if debug: print >>self.tty, "pbm from bw done"
      # try:
      p = subprocess.Popen(autotrace_cmd + [fp.name], stdout=subprocess.PIPE)

      # the following crashes Inkscape (!) when used with GUI and autotrace not installed
      #except Exception as e:
        #print '+ '+' '.join(autotrace_cmd)
        #print e
        #print "Try:\n  sudo apt-get install autotrace"
        #sys.exit(1)

      cand['svg'] = p.communicate()[0]
      if debug: print >>self.tty, "autotrace done"
      if not len(cand['svg']):
        print >>sys.stderr, "autotrace_cmd: " + ' '.join(autotrace_cmd + [fp.name])
        print >>sys.stderr, "ERROR: returned nothing, leaving tmp bmp file around for you to debug"
        cand['svg'] = '<svg/>'                  # empty dummy
      else:
        os.unlink(fp.name)

      # <?xml version="1.0" standalone="yes"?>\n<svg width="86" height="83">\n<path style="stroke:#000000; fill:none;" d="M36 15C37.9219 18.1496 41.7926 19.6686 43.2585 23.1042C47.9556 34.1128 39.524 32.0995 35.179 37.6034C32.6296 40.8328 34 48.1105 34 52M36 17C32.075 22.4565 31.8375 30.074 35 36M74 42L46 38C45.9991 46.1415 46.7299 56.0825 45.6319 64C44.1349 74.7955 23.7094 77.5566 16.044 72.3966C7.27363 66.4928 8.04426 45.0047 16.2276 38.7384C20.6362 35.3626 27.7809 36.0006 33 36M44 37L45 37"/>\n</svg>
      try:
        xml = inkex.etree.fromstring(cand['svg'])
      except:
        print >>sys.stderr, "autotrace_cmd: " + ' '.join(autotrace_cmd + [fp.name])
        print >>sys.stderr, "ERROR: no proper xml returned: '" + cand['svg'] + "'"
        xml = inkex.etree.fromstring('<svg/>')          # empty dummy

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

    if debug: print >>self.tty, "best: %d/%d" % (best_weight_idx, num_attempts)
    ## if standalone:
    # svg = re.sub('stroke:', (stroke_style_add % candidate[best_weight_idx]['strokewidth']) + ' stroke:', candidate[best_weight_idx]['svg'])
    # return svg

    ## inkscape-extension:
    return ( candidate[best_weight_idx]['svg'], candidate[best_weight_idx]['strokewidth'], orig_im_size )


  def calc_unit_factor(self, units='mm'):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        dialog_units = uutounit(self, 1.0, units)
        self.unit_factor = 1.0 / dialog_units
        return self.unit_factor

  def effect(self):
    global debug

    if self.options.version:
      print __version__
      sys.exit(0)
    if self.options.invert         is not None: self.invert_image       = self.options.invert
    if self.options.remove         is not None: self.replace_image      = self.options.remove
    if self.options.megapixels     is not None: self.megapixel_limit    = self.options.megapixels
    if self.options.candidates     is not None: self.candidates         = self.options.candidates
    if self.options.despecle       is not None: self.filter_median      = self.options.despecle
    if self.options.equal_light    is not None: self.filter_equal_light = self.options.equal_light
    if self.options.hairline       is not None: self.hairline           = self.options.hairline
    if self.options.hairline_width is not None: self.hairline_width     = self.options.hairline_width
    # if self.options.debug          is not None: debug                   = self.options.debug
    # self.options.debug = True

    self.calc_unit_factor()

    cliprect = None
    if self.options.cliprect:
      for id, node in self.selected.iteritems():
        if node.tag == inkex.addNS('path','svg'):
          print >>sys.stderr, "Error: id="+str(id)+" is a path.\nNeed a rectangle object for clipping."
        if node.tag == inkex.addNS('rect','svg'):
          if debug: print >>self.tty, "cliprect: id="+str(id), "node="+str(node.tag)
          cliprect = {
            'x': float(node.get('x', 0)),
            'y': float(node.get('y', 0)),
            'w': float(node.get('width', 0)),
            'h': float(node.get('height', 0)),
            'node': node
          }
          if debug: print >>self.tty, "cliprect: id="+str(id), "cliprect="+str(cliprect)

    if not len(self.selected.items()):
      inkex.errormsg(_("Please select an image."))
      return

    if cliprect is not None and len(self.selected.items()) < 2:
      inkex.errormsg(_("Please select an image. Only a cliprect was selected."))
      return

    for id, node in self.selected.iteritems():
      if debug: print >>self.tty, "id="+str(id), "tag="+str(node.tag)
      if self.options.cliprect and node.tag == inkex.addNS('rect','svg'):
        continue
      if node.tag != inkex.addNS('image','svg'):
        inkex.errormsg(_("Object "+id+" is NOT an image. seen:"+str(node.tag)+" expected:"+inkex.addNS('image','svg')+"\n Try - Object->Ungroup"))
        return

      # images can also just have a transform attribute, and no x or y,
      # FIXME: should find the image transformation!
      # could be replaced by a (slower) call to command line, or by computeBBox from simpletransform
      svg_x_off = float(node.get('x', 0))
      svg_y_off = float(node.get('y', 0))
      svg_img_w = float(node.get('width',  0.001))
      svg_img_h = float(node.get('height', 0.001))
      if cliprect is not None:
        # normalize cliprect into range 0..1
        cliprect['x'] = cliprect['x'] - svg_x_off
        cliprect['y'] = cliprect['y'] - svg_y_off
        cliprect['x'] = cliprect['x'] / svg_img_w
        cliprect['y'] = cliprect['y'] / svg_img_h
        cliprect['w'] = cliprect['w'] / svg_img_w
        cliprect['h'] = cliprect['h'] / svg_img_h

      # handle two cases. Embedded and linked images
      # <image .. xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAT8AA ..." preserveAspectRatio="none" height="432" width="425" transform="matrix(1,0,-0.52013328,0.85408511,0,0)"/>
      # <image .. xlink:href="xlink:href="data:image/jpeg;base64,/9j/4AAQSkZJRgAB..."
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
      elif href[:11] == 'data:image/':
        l = href[11:].index(';')
        type = href[11:11+l]			# 'png' 'jpeg'
        if debug: print >>self.tty, "embedded image: "+href[:11+l]
        img=base64.decodestring(href[11+l+8:])
        f=tempfile.NamedTemporaryFile(mode="wb", prefix='centerlinetrace', suffix="."+type, delete=False)
        f.write(img)
        filename=f.name
        f.close()
      else:
        inkex.errormsg(_("Neither file:// nor data:image/; prefix. Cannot parse PNG/JPEG image href "+href[:200]+"..."))
        sys.exit(1)
      if debug: print >>self.tty, "filename="+filename
      #
      path_svg,stroke_width,im_size = self.svg_centerline_trace(filename, cliprect)
      xml = inkex.etree.fromstring(path_svg)
      try:
        path_d=xml.find('path').attrib['d']
      except:
        inkex.errormsg(_("Couldn't trace the path. Please make sure that the checkbox for tracing bright lines is set correctly and that your drawing has enough contrast."))
        sys.exit(1)

      sx = svg_img_w/im_size[0]
      sy = svg_img_h/im_size[1]
      if debug: print >>self.tty, "svg_im_width ",  svg_img_w, "sx=",sx
      if debug: print >>self.tty, "svg_im_height ", svg_img_h, "sy=",sy
      if debug: print >>self.tty, "im_x ", svg_x_off
      if debug: print >>self.tty, "im_y ", svg_y_off
      if debug: print >>self.tty, "pixel_size= ", im_size
      ## map the coordinates of the returned pixel path to the coordinates of the original SVG image.
      if cliprect is not None:
        svg_x_off = max(svg_x_off, float(cliprect['node'].get('x', 0)))
        svg_y_off = max(svg_y_off, float(cliprect['node'].get('y', 0)))
      matrix = "translate(%g,%g) scale(%g,%g)" % (svg_x_off, svg_y_off, sx, sy)
      #
      if href[:5] == 'data:':
        os.unlink(filename) ## it was a temporary file (representing an embedded image).
      #
      # Create SVG Path
      if self.hairline:
        stroke_width = self.hairline_width * 96. / 25.4         # mm2px FIXME: 96dpi is just a default guess.
      else:
        stroke_width = stroke_width * 0.5 * (abs(sx) + abs(sy))
      style = { 'stroke': '#000000', 'fill': 'none', 'stroke-linecap': 'round', 'stroke-width': stroke_width }
      if self.invert_image: style['stroke'] = '#777777'
      path_attr = { 'style': simplestyle.formatStyle(style), 'd': path_d, 'transform': matrix }
      ## insert the new path object
      inkex.etree.SubElement(self.current_layer, inkex.addNS('path', 'svg'), path_attr)
      ## delete the old image object
      if self.replace_image:
        node.getparent().remove(node)
        if cliprect is not None:        # and its cliprect ...
          cliprect['node'].getparent().remove(cliprect['node'])



if __name__ == '__main__':
        e = TraceCenterline()

        e.affect()
        sys.exit(0)    # helps to keep the selection
