inkscape-centerline-trace
=========================

A bitmap vectorizer that can trace along the centerline of a stroke. The builtin inkscape 'trace bitmap' can only trace edges, thus resulting in double lines for most basic use cases.

Download <a href="https://github.com/fablabnbg/inkscape-centerline-trace/releases">Source code and Debian/Ubuntu package</a>

Written with python-Pillow. 
It uses 'autotrace -centerline' and an optimal threshold to vectorize a pixel image.
See centerline-tracing.svg for an illustration of the idea.

In inkscape it shows up under Extensions -> Images -> Centerline Trace ...

<a href="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace-poster.svg"><img src="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace-poster.png" /></a>

Installation hints
------------------
* **Install the extension (all operating systems)**
    * the extension requires the installation of autotrace and python-pil (see below)
    * grab a [binary package](https://github.com/fablabnbg/inkscape-centerline-trace/releases) **or**
    * download the [zip file](https://github.com/fablabnbg/inkscape-centerline-trace/archive/master.zip) of [inkscape-centerline-trace](https://github.com/fablabnbg/inkscape-centerline-trace) and unpack it
    * copy the files centerline-trace.inx, centerline-trace.py to your Inkscape User extensions folder (see Edit > Preferences > System: System info: User extensions)
* **Install autotrace / python-pil**
    * **Windows**
        * Instructions for Inkscape 0.92.2 and higher: 
            * Install autotrace win64-setup.zip version 0.40.0 or later from e.g. https://github.com/autotrace/autotrace/releases
              Make sure the installation path is C:\Program Files (x86)\AutoTrace -- this application searches there.
              - Older version: [autotrace binary](https://github.com/scottvr/autotrace-win64-binaries/raw/master/bin/autotrace.exe) from [autotrace-win64-binaries github repo](https://github.com/scottvr/autotrace-win64-binaries))
                Copy the downloaded autotrace.exe to Inkscape's User extensions folder, that should also work.
        * Instructions for Inkscape 0.92: https://inkscape.org/en/gallery/item/10567/centerline_NIH0Rhk.pdf
    * **MacOS**
        * Install autotrace MacOS.zip version 0.40.0 or later from e.g. https://github.com/autotrace/autotrace/releases
        * open a command line shell to install the python-PIL module:
          + `sudo easy_install install pip`
          + `sudo pip install pillow`
        * open a command line shell to install the inkscape extension:
          + `cd ~/.config/inkscape/extensions`
          + `curl https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace.py -o centerline-trace.py`
          + `curl https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace.inx -o centerline-trace.inx`
        * Please report success in the github issues. As of 2018-08-31, MacOS Support is back, but highly experimental.
    * **GNU/Linux**      
        * Install the autotrace DEB package version 0.40.0 or later from e.g. https://github.com/autotrace/autotrace/releases
        * if you do not have pillow/pil installed, the extension will output an error message prompting you to install it. On Ubuntu and derivatives, run `sudo apt-get install python-pil` to install.
        
* Finally, restart inkscape, and find CenterlineTrace in the `Extensions -> Images` menue.
* Since Inkscape 1.0 the Autotrace library including the CenterlineTrace feature is integrated. That should obsolete this extension. Find an entry in the new `Path -> Trace Bitmap` dialog.

<center><a href="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/testdata/20190528_195103.jpg"><img src="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/testdata/20190528_195103.jpg" width="66%"/></a></center>


Algorithm
---------
The input image is converted to a graymap and histogram normalized with PIL.ImageOps.autocontrast.
Optional preprocessing: equal illumination, median denoise filter.

Autotrace needs a bi-level bitmap. In order to find the
best threshold value, we can run autotrace at multiple thresholds
and evaluate the result candidates.

We count the number of line segments produced and 
measure the total path length drawn.
The svg that has the longest path but the least number of
segments is returned.

<a href="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/testdata/3-images.svg"><img src="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace-3-images-done.png" /></a>
