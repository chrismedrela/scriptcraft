#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.core import direction
from scriptcraft.core.FindPathProblem import FindPathProblem
from scriptcraft.core.GameMap import GameMap
from scriptcraft.utils import *



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
