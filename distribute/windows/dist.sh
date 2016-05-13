#! /bin/bash
# Make a windows distribution

name=$1
vers=$2
out=$3
test -z "$out" && out=.

echo "Creating Windows installer"

[ -d tmp ] && rm -rf tmp
mkdir -p tmp/stream
cp -r files/* tmp/
sed -i -e s@VERSION@"$vers"@g tmp/installer.nsi

pushd tmp
makensis installer.nsi > /dev/null || exit 1
popd
mv tmp/setup.exe $name-$vers-Windows-Installer.exe || exit 1
zip $name-$vers-Windows-Installer.zip $name-$vers-Windows-Installer.exe	# for github upload
rm -rf tmp
mkdir -p $out
mv $name-$vers-Windows-Installer.* $out

