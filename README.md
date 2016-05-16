inkscape-centerline-trace
=========================

A bitmap vectorizer that can trace along the centerline of a stroke. The builtin inkscape 'trace bitmap' can only trace edges, thus resulting in double lines for most basic use cases.

Written with python-Pillow. 
It uses 'autotrace -centerline' and an optimal threshold to vectorize a pixel image.
See centerline-tracing.svg for an illustration of the idea.

Unfinished command line tool. 
Works great with testdata, to be integrated into inkscape.

<p>
<br>
<p>

<a href="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace-poster.svg"><img src="https://raw.githubusercontent.com/fablabnbg/inkscape-centerline-trace/master/centerline-trace-poster.png" /></a>


Algorithm:
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
