inkscape-centerline-trace
=========================

A bitmap vectorizer that can trace along the centerline of a stroke. The builtin inkscape 'trace bitmap' can only trace edges, thus resulting in double lines for most basic use cases.

Written with python-Pillow. 
It uses 'autotrace -centerline' and an optimal threshold to vectorize a pixel image.
See centerline-tracing.svg for an illustration of the idea.

Unfinished command line tool. 
Works great with testdata, to be integrated into inkscape.
