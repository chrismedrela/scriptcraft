#!/usr/bin/env python
#-*- coding:utf-8 -*-


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

    def set_base(self, unit):
        assert unit in self.units
        self.maybe_base = unit

    def remove_unit(self, unit):
        unit.player = None
        self.units.remove(unit)
        if self.maybe_base == unit:
            self.maybe_base = None

    def __str__(self):
        return ("<Player:%d | "
                "color (%d, %d, %d) "
                "started at (%d, %d) "
                "with units {%s}") \
                % (self.ID,
                   self.color[0], self.color[1], self.color[2],
                   self.start_position[0], self.start_position[1],
                   ", ".join(map(lambda unit: str(unit.ID), self.units)))
