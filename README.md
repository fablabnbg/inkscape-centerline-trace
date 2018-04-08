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
* Windows: 
    * Instructions for Inkscape 0.92.2 and higher: 
        * download the [zip file](https://github.com/fablabnbg/inkscape-centerline-trace/archive/master.zip) of [inkscape-centerline-trace](https://github.com/fablabnbg/inkscape-centerline-trace) and unpack it
        * copy the files centerline-trace.inx, centerline-trace.py to your Inkscape User extensions folder (see Edit > Preferences > System: System info: User extensions)
        * download the [autotrace binary](https://github.com/scottvr/autotrace-win64-binaries/raw/master/bin/autotrace.exe) from [autotrace-win64-binaries github repo](https://github.com/scottvr/autotrace-win64-binaries).
        * copy the downloaded autotrace.exe to Inkscape's User extensions folder
    * Instructions for Inkscape 0.92: https://inkscape.org/en/gallery/item/10567/centerline_NIH0Rhk.pdf
* MacOS: (No longer available: http://macappstore.org/autotrace/) Please see https://github.com/fablabnbg/inkscape-centerline-trace/issues/13


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
