#! /bin/bash
# Make a debian/ubuntu distribution

name=$1
vers=$2
url=http://github.com/fablabnbg/inkscape-centerline-trace
requires="autotrace, python3-pil | bash, python-pil"

tmp=../out

[ -d $tmp ] && rm -rf $tmp/*.deb
mkdir $tmp
cp description-pak files
cd files
fakeroot checkinstall --fstrans --reset-uid --type debian \
  --install=no -y --pkgname $name --pkgversion $vers --arch all \
  --pkglicense LGPL --pkggroup other --pakdir ../$tmp --pkgsource $url \
  --pkgaltsource "http://fablab-nuernberg.de" \
  --maintainer "'Juergen Weigert (juewei@fabmail.org)'" \
  --requires "'$requires'" make install \
  -e PREFIX=/usr || { echo "error"; exit 1; }

