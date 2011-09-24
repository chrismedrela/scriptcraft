#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple
import hashlib

from Language import Language

class Program(namedtuple("Program", ('language', 'code'))):
    __slots__ = ()
    
    def sha(self):
        sha = hashlib.sha1()
        sha.update(self.code)
        sha = sha.hexdigest()
        return sha
