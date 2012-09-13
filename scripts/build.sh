#!/bin/bash

# change current directory
dir=`dirname "$0"`
cd "$dir"
cd .. # so we are in scriptcraft root directory

pwd=`pwd`
printf "\nCHANGED CURRENY DIRECTORY TO: ${pwd}\n"

# make README.html
printf '\nRENDERING README.html\n'
. scripts/build_html.sh

# clean up before creating distributions
printf '\nCLEANING BEFORE CREATING DISTRIBUTIONS\n'
rm -r dist
rm -r build
rm `find . | grep ".pyc$"`

# create distribution for windows
printf '\nCREATING WINDOWS DISTRIBUTION\n'
wine C:\\Python27\\python.exe setup.py py2exe > .buildlog_windist
cd dist/py2exe
mkdir games # create empty games directory
printf '\nZIPPING WINDOWS DISTRIBUTION\n'
zip -r zipus.zip . > ../../.buildlog_zipping_windist
mv zipus.zip ../../scriptcraft-for-windows.zip
cd ../..

# clean up
printf '\nCLEANING UP\n'
rm README.html

# finish
printf "\nNOW COMMIT scriptcraft-for-windows.zip.\n"
