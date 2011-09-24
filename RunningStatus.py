#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

class RunningStatus(namedtuple("RunningStatus", ('input', 'output', 'error_output'))):
    __slots__ = ()
