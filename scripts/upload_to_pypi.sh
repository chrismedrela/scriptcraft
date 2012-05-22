#!/bin/bash

printf "COPYING... "

dir=`dirname "$0"`
cd "$dir" # so we are in the same directory where this script is in
cd ../.. # so we are in parent of scriptcraft root directory

TMP=~/tmp
cp -f -r scriptcraft "$TMP"
cd "$TMP/scriptcraft"

printf "OK\n"

# create standard source distribution
python setup.py register sdist upload

# create distributions for windows
wine C:\\Python27\\python.exe setup.py py2exe --target-version=2.7
zip -r scriptcraft-for-windows.zip dist/py2exe