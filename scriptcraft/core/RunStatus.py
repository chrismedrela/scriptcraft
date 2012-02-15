#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple



class RunStatus(namedtuple("RunStatus", ('input',
                                        'output',
                                        'error_output'))):
    __slots__ = ()
