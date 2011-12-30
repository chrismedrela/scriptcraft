#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft.core.actions import StopAction
from scriptcraft.core.cmds import StopCommand



class Unit(object):
    def __init__(self, player, type, position, ID):
        self.program = None
        self.maybe_last_compilation_status = None
        self.maybe_run_status = None
        self.command = StopCommand()
        self.action = StopAction()
        self.position = position
        self.player = player
        self.ID = ID
        self.type = type
        self._minerals = 0
        self.output_messages = []
        self.input_messages = []

    @ property
    def minerals(self):
        return self._minerals

    @ minerals.setter
    def minerals(self, value):
        assert value >= 0
        assert value <= self.type.storage_size or not self.type.has_storage_limit
        self._minerals = value
