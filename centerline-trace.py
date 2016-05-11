#!/usr/bin/env python
#
# Inkscape extension to vectorize bitmaps by tracing along the center of lines
# (C) 2016 juewei@fabmail.org
#
# code snippets visited to learn the extension 'effect' interface:
# - convert2dashes.py
# - http://github.com/jnweiger/inkscape-silhouette
# - http://github.com/jnweiger/inkscape-gears-dev
# - http://sourceforge.net/projects/inkcut/
# - http://code.google.com/p/inkscape2tikz/
# - http://code.google.com/p/eggbotcode/
#
# 2016-05-11 jw, V0.1 -- initial draught

__version__ = '0.1'	# Keep in sync with chain_paths.inx ca line 22
__author__ = 'Juergen Weigert <juewei@fabmail.org>'

import sys, os, tempfile, base64

debug = True
#debug = False

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
import inkex
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

  def version(self):
    return __version__
  def author(self):
    return __author__

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

    self.calc_unit_factor()

    if not len(self.selected.items()):
      inkex.errormsg(_("Please select an image."))
      return

    for id, node in self.selected.iteritems():
      if debug: print >>self.tty, "id="+str(id), "tag="+str(node.tag)
      if node.tag != inkex.addNS('image','svg'):
        inkex.errormsg(_("Object "+id+" is not an image. Try\n  - Object->Ungroup"))
        return
      # handle two cases. Embedded and linked images
      # <image .. xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAT8AA ..." preserveAspectRatio="none" height="432" width="425" transform="matrix(1,0,-0.52013328,0.85408511,0,0)"/>
      # <image  .. xlink:href="file:///home/jw/schaf.png"

      # 
      # 
      # dump the entire svg to file, so that we can examine what an image is.
      href=str(node.get(inkex.addNS('href','xlink')))
      f=open(self.dumpname, 'w')
      f.write(href)
      f.close()
      print >>self.tty, "Dump written to "+self.dumpname
      if href[:7] == 'file://':
        filename=href[7:]
      elif href[:15] == 'data:image/png;':
        png=base64.decodestring(href[15+7:]) 
	f=tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
	f.write(png)
	filename=f.name
      else:
        inkex.errormsg(_("Neither file:// nor data:image/png; prefix. Cannot parse PNG image href "+href))
      print >>self.tty, "filename="+filename
      #
      # do something
      #
      #if href[:5] == 'data:':
      #  os.unlink(filename)
        


if __name__ == '__main__':
        e = TraceCenterline()

        e.affect()
        sys.exit(0)    # helps to keep the selection
