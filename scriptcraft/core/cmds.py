#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Classes *Command represent commands of units. Following command are available:
 StopCommand
 MoveCommand
 ComplexMoveCommand
 ComplexGatherCommand
 FireCommand
 ComplexAttackCommand
 BuildCommand

Attributes of instances of these classes must be accurate type, but
haven't be sensible (for example every string is valid value for unit_type_name).

"""


from collections import namedtuple

from scriptcraft.core import direction



class StopCommand(namedtuple('StopCommand',
                             ())):
    __slots__ = ()

    def __str__(self):
        return '<Command stop>'


class MoveCommand(namedtuple('MoveCommand',
                             ('direction',))):
    __slots__ = ()

    def __str__(self):
        return '<Command move to %s>' \
               % direction.TO_FULL_NAME[self.direction]


class ComplexMoveCommand(namedtuple('ComplexMoveCommand',
                                    ('destination',))):
    __slots__ = ()


    def __str__(self):
        return '<Command move at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class ComplexGatherCommand(namedtuple('ComplexGatherCommand',
                                      ('destination',))):
    __slots__ = ()

    def __str__(self):
        return '<Command gather from (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class FireCommand(namedtuple('FireCommand',
                             ('destination',))):
    __slots__ = ()

    def __str__(self):
        return '<Command fire at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class ComplexAttackCommand(namedtuple('ComplexAttackCommand',
                                      ('destination',))):
    __slots__ = ()

    def __str__(self):
        return '<Command attack at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class BuildCommand(namedtuple('BuildCommand',
                              ('unit_type_name',))):
    __slots__ = ()

    def __str__(self):
        return '<Command build %s>' % self.unit_type_name
