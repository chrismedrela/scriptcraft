#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from Player import Player, PlayerAlreadyHasBase
from Unit import Unit
from UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED


class TestPlayer(unittest.TestCase):

    def test_add_ordinary_unit_and_remove_it(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit()

        player.add_unit(unit)
        self.assertEqual(player.units, [unit])
        self.assertEqual(unit.player, player)

        player.remove_unit(unit)
        self.assertEqual(player.units, [])

    def test_add_unit_as_base_and_remove_it(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit()

        player.add_unit_as_base(unit)
        self.assertEqual(player.maybe_base, unit)

        illegal_operation = lambda: player.add_unit_as_base(unit)
        self.assertRaises(PlayerAlreadyHasBase, illegal_operation)

        player.remove_unit(unit)
        self.assertEqual(player.maybe_base, None)

    def _build_simple_player(self):
        color = (255, 0, 0)
        ID = 7
        result = Player("name", color, ID)
        return result

    def _build_simple_unit(self):
        unit_type = UnitType(attack_range=5,
                             vision_range=10,
                             store_size=0,
                             cost_of_build=5,
                             can_build=False,
                             movable=True,
                             behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                             names=['tank', 't'])
        unit = Unit(unit_type, position=(2, 3), ID=7)
        return unit

if __name__ == '__main__':
    unittest.main()