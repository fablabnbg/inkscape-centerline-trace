#!/bin/bash
echo "Determining Version:"
VERSION=$(sed -ne 's@.*version\s\([a-z0-9\.]*\).*@\1@pi' ../centerline-trace.inx)
echo "Version is: \"$VERSION\""
name=inkscape-centerline-trace
if [ -d $name ]
then
	echo "Removing leftover files"
	rm -rf $name
fi
echo "Copying contents ..."
mkdir $name
cp ../README.md $name/README
cp ../LICENSE* $name/
cp ../centerline-trace-poster.svg $name/
cp ../*.py ../*.inx ../Makefile $name/


echo "****************************************************************"
echo "Ubuntu Version: For Building you must have checkinstall and dpkg"
echo "Build Ubuntu Version (Y/n)?"
read answer
if [ "$answer" != "n" ]
then
  cp -a $name/* deb/files
  (cd deb && sh ./dist.sh $name $VERSION)
fi


rm -rf $name
