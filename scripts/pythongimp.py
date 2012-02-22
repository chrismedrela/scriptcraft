#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os, sys
import subprocess

"""
Run gimp (without windows) and execute python script in it.
First argument is name of file with python script.
"""

def run(file_with_script, cwd=None):
    s = open(file_with_script, 'r')
    skrypt = s.read()
    s.close()
    
    skrypt = skrypt.replace("\"", "\\\"")
  
    polecenie = "gimp -c -n -i -b '(python-fu-eval RUN-INTERACTIVE \""+skrypt+"\")' -b '(gimp-quit 0)'"
    #print polecenie   
    subprocess.call(polecenie, shell=True, cwd=cwd)
    
if __name__ == "__main__":
    run(sys.argv[1])
