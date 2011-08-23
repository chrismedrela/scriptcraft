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
 BuildCommand -- program_object_ID_or_zero to ID obiektu, którego program ma być
  użyty dla nowo budowanej jednostki

Atrybuty tych klas muszą mieć odpowiedni typ, ale nie muszą być sensowne
(może być np. destination=(-2,-3); type_ID musi być poprawnym identyfikatorem
typu i direction musi przyjąć jedną z wartości DIRECTION_*).

"""

from collections import namedtuple


StopCommand = namedtuple('StopCommand', [])
MoveCommand = namedtuple('MoveCommand', ['direction'])
ComplexMoveCommand = namedtuple('ComplexMoveCommand', ['dest_pos'])
ComplexGatherCommand = namedtuple('ComplexGatherCommand', ['dest_pos'])
FireCommand = namedtuple('FireCommand', ['dest_pos'])
ComplexAttackCommand = namedtuple('ComplexAttackCommand', ['dest_pos'])
BuildCommand = namedtuple('BuildCommand', ['unit_type_ID'])

