#!/bin/bash

# change current directory
dir=`dirname "$0"`
cd "$dir"
cd .. # so we are in scriptcraft root directory

pwd=`pwd`
printf "Changed current directory to: ${pwd}\n"

rm -r dist
rm -r build
rm `find . | grep ".pyc$"`

# create distributions for windows
wine C:\\Python27\\python.exe setup.py py2exe
cd dist/py2exe
mkdir games # create empty games directory
zip -r zipus.zip .
mv zipus.zip ../../scriptcraft-for-windows.zip
cd ../..

printf ">>> Now commit scriptcraft-for-windows.zip. <<<\n"
