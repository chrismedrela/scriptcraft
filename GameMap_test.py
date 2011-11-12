#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import copy

from utils import *

from GameMap import GameMap, NoFreeStartPosition, CannotPlaceOnOccupedField


class TestGameMap(unittest.TestCase):

    @ max_time(80, repeat=3)
    def test_constructor(self):
        m = GameMap((128, 128), [(2,3), (4,5)])

    def test_start_positions(self):
        start_positions = ((0,0), (31, 31), (10,12), (22, 22), (23, 3))
        m = GameMap((32, 32), start_positions)
        m.place_unit_at((22, 22), 3)
        m.place_minerals_at((23, 2), 10)

        x, y = m.reserve_next_free_start_position()
        self.assertEqual((x, y), (10, 12))

        illegal_operation = m.reserve_next_free_start_position
        self.assertRaises(NoFreeStartPosition, illegal_operation)

    def test_cannot_place_on_occuped_field(self):
        m = GameMap((16, 16), ())
        m.place_unit_at((8, 9), 4)
        illegal_operation = lambda: m.place_minerals_at((8, 9), 8)
        self.assertRaises(CannotPlaceOnOccupedField, illegal_operation)

    def test_getting_fields(self):
        m = GameMap((16, 16), ())
        m.place_minerals_at((4, 3), 4)
        m.place_unit_at((5, 4), 21)
        m.place_trees_at((6, 5))
        m.place_trees_at((7, 6))
        m.erase_at((7, 6))

        self.assertEqual(m[4][3].has_mineral_deposit(), True)
        self.assertEqual(m[4][3].get_minerals(), 4)
        self.assertEqual(m[5][4].get_unit_ID(), 21)
        self.assertEqual(m[6][5].has_trees(), True)
        self.assertEqual(m[7][6].is_empty(), True)

    @ max_time(150, repeat=3)
    def test_deepcopy_efficiency_and_correctness(self):
        m = GameMap((128, 256), ())
        c = copy.deepcopy(m)

        m.place_unit_at((127,255), 3)
        self.assertEqual(c[127][255].is_empty(), True)

if __name__ == '__main__':
    unittest.main()