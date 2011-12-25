#!/usr/bin/env python
#-*- coding:utf-8 -*-


class PlayerAlreadyHasBase(Exception):
    pass


class Player(object):

    def __init__(self, name, color, ID, start_position):
        self.name = name
        self.color = color
        self.ID = ID
        self.units = []
        self.maybe_base = None
        self.start_position = start_position

    def add_unit(self, unit):
        unit.player = self
        self.units.append(unit)

    def add_unit_as_base(self, unit):
        if self.maybe_base != None:
            raise PlayerAlreadyHasBase()

        self.add_unit(unit)
        self.maybe_base = unit

    def remove_unit(self, unit):
        unit.player = None
        self.units.remove(unit)
        if self.maybe_base == unit:
            self.maybe_base = None

