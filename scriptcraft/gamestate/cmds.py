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

from scriptcraft import direction



class StopCommand(namedtuple('StopCommand',
                             ())):
    __slots__ = ()

    COMMAND_NAMES = ('stop', 's')
    ARGUMENTS = ()

    @staticmethod
    def CONSTRUCTOR():
        return StopCommand()

    def __str__(self):
        return '<Command stop>'


class MoveCommand(namedtuple('MoveCommand',
                             ('direction',))):
    __slots__ = ()

    COMMAND_NAMES = ('move', 'm')
    ARGUMENTS = ('direction',)

    @staticmethod
    def CONSTRUCTOR(d):
        return MoveCommand(d)

    def __str__(self):
        return '<Command move to %s>' \
               % direction.TO_FULL_NAME[self.direction]


class ComplexMoveCommand(namedtuple('ComplexMoveCommand',
                                    ('destination',))):
    __slots__ = ()

    COMMAND_NAMES = ('move', 'm')
    ARGUMENTS = ('int', 'int')

    @staticmethod
    def CONSTRUCTOR(x, y):
        return ComplexMoveCommand((x, y))

    def __str__(self):
        return '<Command move at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class ComplexGatherCommand(namedtuple('ComplexGatherCommand',
                                      ('destination',))):
    __slots__ = ()

    COMMAND_NAMES = ('gather', 'g')
    ARGUMENTS = ('int', 'int')

    @staticmethod
    def CONSTRUCTOR(x, y):
        return ComplexGatherCommand((x, y))

    def __str__(self):
        return '<Command gather from (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class FireCommand(namedtuple('FireCommand',
                             ('destination',))):
    __slots__ = ()

    COMMAND_NAMES = ('fire', 'f')
    ARGUMENTS = ('int', 'int')

    @staticmethod
    def CONSTRUCTOR(x, y):
        return FireCommand((x, y))

    def __str__(self):
        return '<Command fire at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class ComplexAttackCommand(namedtuple('ComplexAttackCommand',
                                      ('destination',))):
    __slots__ = ()

    COMMAND_NAMES = ('attack', 'a')
    ARGUMENTS = ('int', 'int')

    @staticmethod
    def CONSTRUCTOR(x, y):
        return ComplexAttackCommand()

    def __str__(self):
        return '<Command attack at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class BuildCommand(namedtuple('BuildCommand',
                              ('unit_type_name',))):
    __slots__ = ()

    COMMAND_NAMES = ('build', 'b')
    ARGUMENTS = ('str',)

    @staticmethod
    def CONSTRUCTOR(t):
        return BuildCommand(t)

    def __str__(self):
        return '<Command build %s>' % self.unit_type_name


ALL_COMMANDS = [StopCommand, MoveCommand, ComplexMoveCommand,
                ComplexGatherCommand, FireCommand,
                ComplexAttackCommand, BuildCommand]
