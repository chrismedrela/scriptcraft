#!/usr/bin/env python
#-*- coding:utf-8 -*-

import hashlib
from collections import namedtuple



class Program(namedtuple("Program", ('language',
                                     'code'))):
    __slots__ = ()

    def sha(self):
        sha = hashlib.sha1()
        sha.update(self.code)
        sha = sha.hexdigest()
        return sha
