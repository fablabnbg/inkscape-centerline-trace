#! /bin/bash
# Make a windows binary

disttop=$(readlink -e $(dirname $0))	# abspath(dir)

APP_NAME=$1
APP_VERSION=$2

if [ -z "$APP_VERSION" ]; then
  echo "Usage: $0 APP_NAME APP_VERSION"
  exit 1
fi

cd $disttop
makensis -DVERSION=$APP_VERSION-$(date +%Y%m%d) $APP_NAME.nsi
mkdir -p ../out
zip=../out/$APP_NAME-$APP_VERSION-$(date +%Y%m%d)-win64-setup.zip
rm -f  $zip
zip -r $zip $APP_NAME-*-setup.exe
cp $APP_NAME-*-setup.exe ../out

