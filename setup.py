#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages
from scriptcraft.utils import datafile_path
import os, sys

# that ugly trick solve problem with encoding of README file
import sys
reload(sys).setdefaultencoding("UTF-8")

PROJECT_NAME = 'scriptcraft'
DIRECTORIES_WITH_DATA_FILES = ('graphic', 'maps')

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

def _find_packages():
    packages = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_NAME):
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'):
                del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(_fullsplit(dirpath)))
    return packages

def _find_data_files():
    data_files = []
    for directory in DIRECTORIES_WITH_DATA_FILES:
        for dirpath, dirnames, filenames in os.walk(directory):
            for i, dirname in enumerate(dirnames):
                if dirname.startswith('.'):
                    del dirnames[i]
            if '__init__.py' in filenames:
                pass
            elif filenames:
                data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])
    data_files.append(('.', ['LICENSE.txt']))
    return data_files

def _is_it_py2exe_compilation():
    return 'py2exe' in sys.argv

if __name__ == "__main__":
    packages = _find_packages()
    data_files = _find_data_files()

    if _is_it_py2exe_compilation():
        print 'Detected py2exe installation/building.'
        import py2exe
        drive_c_path = r'Z:\\home\\krzysiumed\\.wine\\drive_c\\'
        python_version = sys.version_info[0:2] # for example (2, 6)
        python_version = "".join(map(str, python_version)) # for example "26"
        assert python_version in ('26', '27'), ('Is it valid python version? ' +
                                                python_version)
        python_path = drive_c_path + "Python" + python_version + r'\\'
        dlls = [
            drive_c_path + r'windows\\system32\\python%s.dll' % python_version,
            python_path + r'DLLs\\tcl85.dll',
            python_path + r'DLLs\\tk85.dll',
        ]
        data_files += [('.', dlls)]
        data_files += [('.', [os.path.join('onlywindows', 'configuration.ini')])]
    else:
        print 'Detected non-py2exe installation/building.'
        data_files += [('.', ['configuration.ini'])]

    kwargs = dict(
        name=PROJECT_NAME,
        version='0.2.0.a1',
        author = "Krzysztof Medrela",
        author_email = "krzysiumed@gmail.com",
        description = "Scriptcraft programming game - program your units to fight against other players.",
        long_description = open(datafile_path('README.rst'), 'r').read(),
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
        include_package_data = False,
        data_files = data_files,
        options = {
            'py2exe' : {'includes':['Tkinter', 'tkFileDialog'],
                        'bundle_files':2,
                        'dist_dir':'dist/py2exe'},
        },
        entry_points = {
            'gui_scripts': [
                'scriptcraft = scriptcraft.client:run',
            ],
        },
    )

    if _is_it_py2exe_compilation():
        kwargs['zipfile'] = None
        kwargs['windows'] = [
            {'script':'scriptcraft/client.py',
             'dest_base':'scriptcraft'},
        ]

    setup(**kwargs)

