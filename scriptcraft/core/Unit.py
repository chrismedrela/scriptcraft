#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft.core.cmds import StopCommand
from scriptcraft.core.actions import StopAction

class Unit(object):
    def __init__(self, player, type, position, ID):

        self.program = None
        self.maybe_last_compilation_status = None
        self.maybe_run_status = None
        self.execution_status = None
        self.command = StopCommand()
        self.action = StopAction()
        self.position = position
        self.player = player
        self.ID = ID
        self.type = type
        self.minerals = 0
        self.output_messages = []
        self.input_messages = []