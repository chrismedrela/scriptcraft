#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import unittest

from scriptcraft import direction
from scriptcraft.gamemap import (GameMap, FindPathProblem, Field,
                                 NoFreeStartPosition, FieldIsOccupied)
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


class TestField(unittest.TestCase):
    def test_trees(self):
        field = Field(trees=True)

        self.assertFalse(field.is_empty())
        self.assertFalse(field.is_flat_and_empty())
        self.assertTrue(field.has_trees())
        self.assertFalse(field.has_unit())

    def test_unit(self):
        field = Field(unit_ID=667)

        self.assertFalse(field.is_empty())
        self.assertFalse(field.has_trees())
        self.assertTrue(field.has_unit())
        self.assertEqual(field.get_unit_ID(), 667)

    def test_minerals_and_flat(self):
        field = Field(minerals=0)

        self.assertFalse(field.is_empty())
        self.assertTrue(field.is_flat())
        self.assertTrue(field.has_mineral_deposit())
        self.assertFalse(field.has_trees())
        self.assertEqual(field.get_minerals(), 0)

    def test_trees_and_unit(self):
        self.assertRaises(
            ValueError,
            lambda: Field(trees=True, unit_ID=1)
        )

    def test_erased_field(self):
        field = Field(trees=True)
        field = field.Erased()

        self.assertTrue(field.is_empty())
        self.assertTrue(field.is_flat_and_empty())
        self.assertFalse(field.has_trees())

    def test_placed_unit(self):
        field = Field(trees=True)
        field = field.PlacedUnit(unit_ID=123)

        self.assertFalse(field.has_trees())
        self.assertEqual(field.get_unit_ID(), 123)

    def test_place_on_occupied_field_allowed(self):
        field = Field(minerals=2)
        field = field.PlacedTrees()

    def test_repr(self):
        field = Field(upland=True, unit_ID=123)

        self.assertEqual(repr(field),
                         '<Field(type=2, arg=123) : upland with unit 123>')

    def test_deep_copy(self):
        field = Field(unit_ID=123)
        field_copy = copy.deepcopy(field)
        self.assertEqual(field, field_copy)


class TestFieldEfficiency(unittest.TestCase):

    @ max_time(10)
    def test_function_is_empty(self):
        f = Field(minerals=2)
        for _ in xrange(64*64):
            f.is_empty()

    @ max_time(50)
    def test_constructor_placed_minerals(self):
        f = Field(trees=True)
        for _ in xrange(64*64):
            f.PlacedMinerals(123)


class TestFindingPath(unittest.TestCase):
    def test_destination_equal_to_source(self):
        self.game_map = GameMap((4, 4))
        self.source = self.destination = (3, 2)

        expected_direction = None
        self._test_answer_equal_to(expected_direction)

    def test_destination_is_source_neighbour(self):
        self.game_map = GameMap((4, 4))
        self.source = (3, 2)
        self.destination = (3, 3)

        expected_direction = direction.S
        self._test_answer_equal_to(expected_direction)

    def test_destination_is_unavaiable_but_its_neighbour_is_not(self):
        s = 'tu    \n' + \
            'ttttt \n' + \
            '      \n' + \
            ' ttttt\n' + \
            ' t    \n' + \
            '   tt*'
        self.game_map = self._create_game_map_from_text(s)

        self.destination = (1, 0)
        expected_direction = direction.N
        self._test_answer_equal_to(expected_direction)

    def test_destination_is_far_far_away_but_is_avaiable(self):
        size = 128
        self.game_map = GameMap((size, size))
        self.source = 14, 0
        self.destination = 14+size/2, size-1

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction in (direction.E, direction.S))

    def test_destination_is_unavailable_nor_its_neighbours(self):
        s = ' t  \n' + \
            ' t  \n' + \
            '*t  \n' + \
            ' t^ '
        self.game_map = self._create_game_map_from_text(s)

        expected_direction = None
        self._test_answer_equal_to(expected_direction)

    def test_road_block(self):
        s = '                         \n' + \
            '  ^                      \n' + \
            '                         \n' + \
            '                         \n' + \
            '                         \n' + \
            ' tt                      \n' + \
            ' t t                     \n' + \
            'tt tttttttttttttt        \n' + \
            '     ttttttttttttt       \n' + \
            '    ttttttttttttttt      \n' + \
            '      tttttttttttt       \n' + \
            '        tttttttttt       \n' + \
            '         ttttttttt       \n' + \
            '                tt       \n' + \
            '                tt       \n' + \
            '    *           tt       \n' + \
            '                tt       \n' + \
            '                tt       \n' + \
            '                         \n' + \
            '                         '
        self.game_map = self._create_game_map_from_text(s)

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction in (direction.E, direction.S))

    def test_destination_is_unavailable_but_its_neighbours_are_not(self):
        s = '*u'
        self.destination = (1, 0)
        self.game_map = self._create_game_map_from_text(s)

        self._test_answer_equal_to(None)

    def test_destination_behind_border(self):
        self.game_map = GameMap((3, 3), ())
        self.destination = (3, 0)
        self.source = (2, 0)

        self._test_answer_equal_to(None)

    def test_skip_if_too_long_searching_time(self):
        size = 256
        s = (' ttttttttttttttttttttttttttttttt\n'*1 + \
             '                                \n'*10 + \
             'ttttttttttttttttttttttttttttttt \n'*1)*5
        s = s[:-1] # delete last '\n'
        self.game_map = self._create_game_map_from_text(s)
        self.destination = (0, 0)
        self.source = (0, (1+10+1)*4)

        self._test_answer_equal_to(None)
        assert self.problem.iteration == FindPathProblem.ITERATIONS_LIMIT

    @ max_time(10)
    def test_efficiency_on_blank_map_with_non_heura_algorythm(self):
        size_of_map = FindPathProblem.MIN_DISTANCE_TO_USE_HEURA/2-1
        self._test_efficiency_on_blank_map(size_of_map)
        assert distance(self.source, self.destination) < FindPathProblem.MIN_DISTANCE_TO_USE_HEURA

    @ max_time(150)
    def test_efficiency_on_blank_map_with_heura_algorythm(self):
        size_of_map = 128
        self._test_efficiency_on_blank_map(size_of_map)
        assert distance(self.source, self.destination) >= FindPathProblem.MIN_DISTANCE_TO_USE_HEURA

    def _test_efficiency_on_blank_map(self, size_of_map):
        self.game_map = GameMap((size_of_map, size_of_map))
        self.source = size_of_map-1, 0
        self.destination = 0, size_of_map-1

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction != None)

    def _create_game_map_from_text(self, s):
        """ '*' means source and '^' - destination """

        split = s.split('\n')

        size_x, size_y = len(split[0]), len(split)

        m = GameMap((size_x, size_y), ())

        switch = {' ': lambda position: None,
                  't': lambda position: m.place_trees_at(position),
                  'u': lambda position: m.place_unit_at(position, 1),
                  '*': lambda position: setattr(self, 'source', position),
                  '^': lambda position: setattr(self, 'destination', position),}
        for y, line in enumerate(split):
            for x, char in enumerate(line):
                case = switch[char]
                case((x, y))

        return m

    def _test_answer_equal_to(self, expected_direction):
        answered_direction = self._find_direction()
        self.assertEqual(expected_direction, answered_direction)

    def _find_direction(self):
        self.problem = FindPathProblem(self.source, self.destination, self.game_map)
        answer = self.problem.find_direction()
        return answer

