#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Launch it inside gimp. Use pythongimp.py.
"""

import os
from os import getcwd
from glob import glob
from gimpfu import *

DOCELOWE_ROZSZERZENIE = ".png"
  
def run(folder=None):
    folder = folder or getcwd()
    pattern = "*.xcf"
    files = glob(os.path.join(folder, pattern))
    for filename in files:
        image = pdb.gimp_file_load(filename, filename)

        #pdb.gimp_image_flatten(image)
        pdb.gimp_image_merge_visible_layers(image, 1)

        drawable = pdb.gimp_image_get_active_layer(image)
        new_filename = filename[:-4]+DOCELOWE_ROZSZERZENIE
        pdb.gimp_file_save(image, drawable, new_filename, new_filename)
        pdb.gimp_image_delete(image)
        print filename, "-->", new_filename
        
    
if __name__ == "__main__":
    run()

