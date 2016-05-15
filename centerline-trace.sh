#!/bin/sh
# shell script wrapper to run an inkscape extension 
# as a standaloine tool

image=$1 
test -z "$image" && image=testdata/kringel.png
case "$image" in .*) ;; /*) ;; *) image=./$image;; esac
tmpsvg=/tmp/$$-centerline-trace-wrapper.svg

cat << EOF > $tmpsvg
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns="http://www.w3.org/2000/svg"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
   xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   width="210mm"
   height="297mm"
   viewBox="0 0 210 297">
  <g
     inkscape:label="Ebene 1"
     inkscape:groupmode="layer"
     id="layer1">
    <image
       sodipodi:absref="$image"
       xlink:href="$image"
       width="1456.2667"
       height="819.15002"
       preserveAspectRatio="none"
       id="image4421"
       x="-577.12152"
       y="-226.81631" />
  </g>
</svg>
EOF

python centerline-trace.py --id=image4421 $tmpsvg
#rm $tmpsvg
