#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages
from scriptcraft.utils import datafile_path
import os

# that ugly trick solve problem with encoding of README file
import sys
reload(sys).setdefaultencoding("UTF-8")

PROJECT_NAME = 'scriptcraft'

def _fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return _fullsplit(head, [tail] + result)

def _find_packages_and_data_files():
    packages = []
    data_files = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_NAME):
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(_fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])
    return packages, data_files

if __name__ == "__main__":
    packages, _ = _find_packages_and_data_files()
    setup(
        name=PROJECT_NAME,
        version='0.1.27',
        author = "Krzysztof Medrela",
        author_email = "krzysiumed@gmail.com",
        description = "Scriptcraft programming game - program your units to fight against other players.",
        long_description = open(datafile_path('../README.rst'), 'r').read(),
        license = "GPLv3",
        keywords = [PROJECT_NAME, 'programming game', 'game'],
        url = "http://github.com/krzysiumed/scriptcraft",
        classifiers = [
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Natural Language :: Polish",
            "Operating System :: Unix",
            "Programming Language :: Python :: 2.6",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 2 :: Only",
            "Topic :: Games/Entertainment",
        ],

        install_requires = [
            'PIL==1.1.7',
        ],
        packages = packages,
        include_package_data = True,
        entry_points = {
            'gui_scripts': [
                'scriptcraft = scriptcraft.client:run',
            ],
        },
    )
