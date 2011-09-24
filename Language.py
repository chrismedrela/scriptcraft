#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

class Language(namedtuple('Language', ('ID', 'name', 'source_extension', 'binary_extension', 'compilation_command', 'running_command'))):
    __slots__ = ()
    
    @property
    def source_file_name(self):
        return 'src' + self.source_extension
        
    @property
    def binary_file_name(self):
        return 'bin' + self.binary_extension
