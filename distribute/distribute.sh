#!/bin/bash

cd $(dirname $0)

echo "Determining Version:"
VERSION=$(sed -ne 's@.*version\s\([a-z0-9\.]*\).*@\1@pi' ../centerline-trace.inx)
echo "Version is: \"$VERSION\""
name=inkscape-centerline-trace
rm -rf $name

echo "Copying contents ..."
mkdir -p $name
cp ../README.md $name/README
cp ../LICENSE* $name/
cp ../centerline-trace-poster.svg $name/
cp ../*.py ../*.inx ../Makefile $name/


echo "****************************************************************"
echo "Ubuntu Version: needs checkinstall and dpkg"
echo "Build Ubuntu Version (Y/n)?"
read answer
if [ "$answer" != "n" ]; then
  mkdir -p deb/files
  cp -a $name/* deb/files
  (cd deb && sh ./dist.sh $name $VERSION)
fi

echo "****************************************************************"
echo "Windows Version: needs makensis"
echo "Build Windows Version (Y/n)?"
read answer
if [ "$answer" != "n" ]; then
  (cd win && sh ./dist.sh $name $VERSION)
fi


echo "Built packages are in distribute/out :"
ls -la out
echo "Cleaning up..."
rm -rf $name
echo "done."
