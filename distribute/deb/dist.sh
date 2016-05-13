#! /bin/bash
# Make a debian/ubuntu distribution

name=$1
vers=$2
out=$3
test -z "$out" && out=.

[ -d tmp ] && rm -rf tmp
mkdir tmp
cd files
fakeroot checkinstall --fstrans --reset-uid --type debian --install=no -y --pkgname $name --pkgversion $vers --arch all --pkglicense LGPL --pkggroup other --pkgsource "http://github.com/fablabnbg/inkscape-chain-paths" --pkgaltsource "http://fablab-nuernberg.de" --pakdir tmp/ --maintainer "'Juergen Weigert (juewei@fabmail.org)'" --requires "bash" make install -e PREFIX=/usr > /dev/null || { echo "error"; exit 1; }
mkdir -p $out
mv tmp/*.deb $out
rm -rf tmp

