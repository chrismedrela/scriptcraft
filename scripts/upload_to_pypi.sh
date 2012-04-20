#!/bin/bash

printf "COPYING... "

dir=`dirname "$0"`
cd "$dir" # so we are in the same directory where this script is in
cd ../.. # so we are in parent of scriptcraft root directory

TMP=~/tmp
cp -f -r scriptcraft "$TMP"
cd "$TMP/scriptcraft"

printf "OK\n"

python setup.py register sdist upload

# we dropped windows support
#wine C:\\Python26\\python.exe setup.py register bdist_wininst --target-version=2.6 upload
#wine C:\\Python27\\python.exe setup.py register bdist_wininst --target-version=2.7 upload