#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.core.Player import Player
from scriptcraft.core.Unit import Unit
from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED



class TestPlayer(unittest.TestCase):
    def test_add_base_and_remove_it(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit(player)

        player.add_unit(unit)
        player.set_base(unit)
        self.assertEqual(unit.player, player)
        self.assertEqual(player.units, [unit])
        self.assertEqual(player.maybe_base, unit)

        player.remove_unit(unit)
        self.assertEqual(player.units, [])
        self.assertEqual(player.maybe_base, None)
        self.assertEqual(unit.player, None)

    def test_to_str(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit(player)
        player.add_unit(unit)

        expected = ("<Player:14 | color (255, 0, 0) started at (3, 4) "
                    "with units {7}")
        self.assertEqual(expected, str(player))

    def _build_simple_player(self):
        color = (255, 0, 0)
        ID = 14
        start_position = (3, 4)
        result = Player("name", color, ID, start_position)
        return result

    def _build_simple_unit(self, player):
        unit_type = UnitType(attack_range=5,
                             vision_radius=10,
                             storage_size=0,
                             build_cost=5,
                             can_build=False,
                             movable=True,
                             behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                             names=['tank', 't'])
        unit = Unit(player=player, type=unit_type, position=(2, 3), ID=7)
        return unit
