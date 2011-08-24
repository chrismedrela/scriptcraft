#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Klasy *Command reprezentują polecenia wydane jednostkom. Są to:
 StopCommand
 MoveCommand
 ComplexMoveCommand
 ComplexGatherCommand
 FireCommand
 ComplexAttackCommand
 BuildCommand

Atrybuty tych klas muszą mieć odpowiedni typ, ale nie muszą być sensowne
(może być np. destination=(-2,-3); direction musi przyjąć jedną z wartości
direction.*; unit_type_name to dowolny string).

"""

from collections import namedtuple


StopCommand = namedtuple('StopCommand', [])
MoveCommand = namedtuple('MoveCommand', ['direction'])
ComplexMoveCommand = namedtuple('ComplexMoveCommand', ['dest_pos'])
ComplexGatherCommand = namedtuple('ComplexGatherCommand', ['dest_pos'])
FireCommand = namedtuple('FireCommand', ['dest_pos'])
ComplexAttackCommand = namedtuple('ComplexAttackCommand', ['dest_pos'])
BuildCommand = namedtuple('BuildCommand', ['unit_type_name'])

