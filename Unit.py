#!/usr/bin/env python
#-*- coding:utf-8 -*-

class Unit(object):
    def __init__(self, type, position):

        self.program = None
        self.maybe_last_compilation_status = None
        self.maybe_run_status = None
        self.execution_status = None
        self.command = None
        self.action = None
        self.position = position
        self.player = None
        self.ID = None
        self.type = type
        self.minerals = 0
        self.output_messages = None
        self.input_messages = None