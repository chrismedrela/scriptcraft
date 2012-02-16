#!/usr/bin/env python
#-*- coding:utf-8 -*-

from copy import deepcopy
import unittest

from scriptcraft.core.Player import Player
from scriptcraft.core.Program import STAR_PROGRAM
from scriptcraft.core.Unit import Unit
from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED
from scriptcraft.utils import *



class TestUnit(unittest.TestCase):
    def test_to_str(self):
        unit_type = self._build_simple_unit_type()
        player = self._build_simple_player()
        unit = Unit(player=player, type=unit_type, position=(2, 3), ID=7)
        unit.program = STAR_PROGRAM

        expected = ("<Unit:7 | tank of player 14 at (2, 3) "
                    "with star program with <Command stop> "
                    "doing <Action stop>>")
        self.assertEqual(str(unit), expected)

    def _build_simple_unit_type(self):
        return UnitType(attack_range=5,
                        vision_radius=10,
                        storage_size=0,
                        build_cost=5,
                        can_build=False,
                        movable=True,
                        behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                        names=['tank', 't'])

    def _build_simple_player(self):
        color = (255, 0, 0)
        ID = 14
        start_position = (3, 4)
        result = Player("name", color, ID, start_position)
        return result
