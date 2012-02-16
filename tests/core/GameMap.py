#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import unittest

from scriptcraft.core.GameMap import (GameMap, NoFreeStartPosition,
                                      FieldIsOccupied)
from scriptcraft.utils import *



class TestGameMap(unittest.TestCase):
    @ max_time(100, repeat=1)
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
        self.assertRaises(FieldIsOccupied, illegal_operation)

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

        self.assertEqual(m.get_field((7, 6)), m[7][6])

    def test_find_flat_and_free_neighbour_when_it_doesnt_exist(self):
        m = GameMap((4, 4), ())
        m.place_trees_at((1, 0))
        m.place_trees_at((0, 1))

        neighbour = m.find_flat_and_free_neighbour_of((0, 0))
        expected_neighbour = None
        self.assertEqual(neighbour, expected_neighbour)

    def test_is_valid_position(self):
        m = GameMap((8, 8), ())
        self.assertFalse(m.is_valid_position((8, 4)))

    @ max_time(200, repeat=1)
    def test_deepcopy_efficiency_and_correctness(self):
        start_positions = [(3, 3), (4, 5)]
        m = GameMap((128, 256), start_positions)
        c = copy.deepcopy(m)

        m.place_unit_at((127,255), 3)
        self.assertEqual(c[127][255].is_empty(), True)

        assert m._free_start_positions == c._free_start_positions
        m.reserve_next_free_start_position()
        self.assertNotEqual(m._free_start_positions, c._free_start_positions)
