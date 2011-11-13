#!/usr/bin/env python
#-*- coding:utf-8 -*-

from cmds import StopCommand
from actions import StopAction

class Unit(object):
    def __init__(self, type, position, ID):

        self.program = None
        self.maybe_last_compilation_status = None
        self.maybe_run_status = None
        self.execution_status = None
        self.command = StopCommand()
        self.action = StopAction()
        self.position = position
        self.player = None
        self.ID = ID
        self.type = type
        self.minerals = 0
        self.output_messages = []
        self.input_messages = []