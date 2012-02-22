#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Build graphic from .xcf files in graphic.
"""

from glob import glob
import os
import pythongimp
import shutil


GRAPHIC_SOURCE = '../graphics'
GRAPHIC_DESTINATION = '../scriptcraft/graphic'

def _copy_files():
    pattern = "*.png"
    folder = GRAPHIC_SOURCE
    files = glob(os.path.join(folder, pattern))
    for filename in files:
        print 'moving', filename, 
        try:
            shutil.move(filename, GRAPHIC_DESTINATION)
        except shutil.Error:
            print '-- OVERWRITTING!', 
            try:
                shutil.copy(filename, GRAPHIC_DESTINATION)
                os.remove(filename)
            except (shutil.Error, IOError):
                print '-- ERROR!'
            else:
                print '-- OK'
        else:
            print '-- OK'

def run():
    pythongimp.run('xcf2png.py', GRAPHIC_SOURCE)
    _copy_files()
    

if __name__ == "__main__":
    run()
