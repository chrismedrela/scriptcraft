#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple



class Language(namedtuple('Language', ('ID',
                                       'name',
                                       'source_extension',
                                       'binary_extension',
                                       'compilation_command',
                                       'running_command'))):
    __slots__ = ()

    @property
    def source_file_name(self):
        return 'src' + self.source_extension

    @property
    def binary_file_name(self):
        return 'bin' + self.binary_extension


DEFAULT_CPP_LANGUAGE = Language(
    ID='cpp',
    name='c++',
    source_extension='.cpp',
    binary_extension='.exe',
    compilation_command='g++ src.cpp -o bin.exe',
    running_command='./bin.exe',
)
DEFAULT_PYTHON_LANGUAGE = Language(
    ID='py',
    name='python',
    source_extension='.py',
    binary_extension='.py',
    compilation_command='cp src.py bin.py',
    running_command='python bin.py',
)
