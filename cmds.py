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

class StopCommand(namedtuple('StopCommand', ())):
    __slots__ = ()

class MoveCommand(namedtuple('MoveCommand', ('direction',))):
    __slots__ = ()

class ComplexMoveCommand(namedtuple('ComplexMoveCommand', ('dest_pos',))):
    __slots__ = ()

class ComplexGatherCommand(namedtuple('ComplexGatherCommand', ('dest_pos',))):
    __slots__ = ()

class FireCommand(namedtuple('FireCommand', ('dest_pos',))):
    __slots__ = ()

class ComplexAttackCommand(namedtuple('ComplexAttackCommand', ('dest_pos',))):
    __slots__ = ()

class BuildCommand(namedtuple('BuildCommand', ('unit_type_name',))):
    __slots__ = ()

