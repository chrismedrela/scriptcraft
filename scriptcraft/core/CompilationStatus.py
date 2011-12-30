#!/usr/bin/env python
#-*- coding:utf-8 -*-


from collections import namedtuple


class CompilationStatus(namedtuple("CompilationStatus",
                                   ('output', 'error_output'))):
    __slots__ = ()
