#! /bin/bash
# Make a debian/ubuntu distribution

name=$1
vers=$2
url=http://github.com/fablabnbg/inkscape-centerline-trace
requires="autotrace, python3-PIL | bash, python-PIL"

tmp=../out

[ -d $tmp ] && rm -rf $tmp/*.deb
mkdir $tmp
cd files
fakeroot checkinstall --fstrans --reset-uid --type debian \
  --install=no -y --pkgname $name --pkgversion $vers --arch all \
  --pkglicense LGPL --pkggroup other --pakdir ../$tmp --pkgsource $url \
  --pkgaltsource "http://fablab-nuernberg.de" \
  --maintainer "'Juergen Weigert (juewei@fabmail.org)'" \
  --requires "'$requires'" make install \
  -e PREFIX=/usr || { echo "error"; exit 1; }

