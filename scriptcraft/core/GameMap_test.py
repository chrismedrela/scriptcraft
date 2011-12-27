#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import copy

from scriptcraft.core import direction
from scriptcraft.core.GameMap import GameMap, NoFreeStartPosition, FieldIsOccupied
from scriptcraft.core.FindPathProblem import FindPathProblem
from scriptcraft.utils import *



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

    @ max_time(150, repeat=3)
    def test_deepcopy_efficiency_and_correctness(self):
        m = GameMap((128, 256), ())
        c = copy.deepcopy(m)

        m.place_unit_at((127,255), 3)
        self.assertEqual(c[127][255].is_empty(), True)

class TestFindingPath(unittest.TestCase):

    def test_destination_equal_to_source(self):
        s = '    \n' + \
            '    \n' + \
            '    \n' + \
            '    '
        m = self._create_game_map_from_text(s)

        source = destination = (3, 2)
        excepted_direction = None
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertEqual(excepted_direction, answered_direction)


    def test_destination_is_source_neightbour(self):
        s = '    \n' + \
            '    \n' + \
            '    \n' + \
            '    '
        m = self._create_game_map_from_text(s)

        source = (3, 2)
        destination = (3, 3)
        excepted_direction = direction.S
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertEqual(excepted_direction, answered_direction)


    def test_destination_is_unavaiable_but_its_neightbour_is_not(self):
        s = 'tu    \n' + \
            'ttttt \n' + \
            '      \n' + \
            ' ttttt\n' + \
            ' t    \n' + \
            '   tt '
        m = self._create_game_map_from_text(s)

        source = (5, 5)
        destination = (1, 0)
        excepted_direction = direction.N
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertEqual(excepted_direction, answered_direction)


    def test_destination_is_far_far_away_but_is_avaiable(self):
        size = 128
        m = GameMap((size, size))
        source = 14, 0
        destination = 14+size/2, size-1
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertTrue(answered_direction in (direction.E, direction.S))


    def test_destination_is_unavailable_nor_its_neightbours(self):
        s = ' t  \n' + \
            ' t  \n' + \
            ' t  \n' + \
            ' t  '
        m = self._create_game_map_from_text(s)

        source = (0, 2)
        destination = (2, 3)
        excepted_direction = None
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertEqual(excepted_direction, answered_direction)


    @ max_time(10)
    def test_efficiency_on_blank_map_with_non_heura_algorythm(self):
        size = FindPathProblem.MIN_DISTANCE_TO_USE_HEURA/2-1
        m = GameMap((size, size))
        source = size-1, 0
        destination = 0, size-1
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertTrue(answered_direction != None)


    @ max_time(150)
    def test_efficiency_on_blank_map_with_heura_algorythm(self):
        size = 128
        assert FindPathProblem.MIN_DISTANCE_TO_USE_HEURA <= size
        m = GameMap((size, size))
        source = 0, 0
        destination = size-1, size-1
        answered_direction = m.find_direction_of_path_from_to(source, destination)
        self.assertTrue(answered_direction != None)


    def _create_game_map_from_text(self, s):
        split = s.split('\n')

        size_x, size_y = len(split[0]), len(split)

        m = GameMap((size_x, size_y), ())

        switch = {' ': lambda position: None,
                  't': lambda position: m.place_trees_at(position),
                  'u': lambda position: m.place_unit_at(position, 1)}
        for y, line in enumerate(split):
            for x, char in enumerate(line):
                case = switch[char]
                case((x, y))

        return m



if __name__ == '__main__':
    unittest.main()