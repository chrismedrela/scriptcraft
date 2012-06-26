#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import unittest

from scriptcraft import direction
from scriptcraft.gamemap import (GameMap, Field, _FindPathProblem,
                                 FieldOutsideMap, FieldIsOccupied)
from scriptcraft.utils import *



class TestGameMapAndField(unittest.TestCase):
    def test_creating_and_getting_and_setting_fields(self):
        game_map = GameMap(size=(16, 16), start_positions=[(5, 6), (7, 8)])

    def test_getting_empty_field(self):
        game_map = GameMap((16, 16), [])
        field = game_map[9, 6]

        self.assertEqual(field.ground_type, 1)
        self.assertEqual(field.valid_position, True)
        self.assertEqual(field.position, (9, 6))
        self.assertEqual(field.maybe_object, None)
        self.assertEqual(field.accessible, True)
        self.assertEqual(field.empty, True)

    def test_changing_ground_type_of_field(self):
        game_map = GameMap((16, 16), [])
        field = game_map[9, 6]
        field.change_ground(2)
        self.assertEqual(game_map[9, 6].ground_type, 2)

    def test_placing_object_on_field(self):
        game_map = GameMap((16, 16), [])
        field = game_map[9, 6]
        obj = object()
        field.place_object(obj)
        self.assertEqual(field.accessible, False)
        self.assertEqual(field.empty, False)
        self.assertEqual(field.maybe_object, obj)
        self.assertEqual(field, game_map[9, 6])

    def test_setting_field_with_object(self):
        game_map = GameMap((16, 16), [])
        field = game_map[9, 6]
        field.place_object(object())

        field = game_map[9, 6]
        game_map[9, 6] = field # shouldn't raise error

    def test_remove_from_field_non_existing_object(self):
        game_map = GameMap((16, 16), [])
        empty_field = game_map[9, 6]
        empty_field.place_object(None) # allowed

    def test_cannot_place_on_occuped_field(self):
        game_map = GameMap((16, 16), [])
        game_map[9, 6].place_object(object())
        illegal_operation = lambda: game_map[9, 6].place_object(object())
        self.assertRaises(FieldIsOccupied, illegal_operation)

    def test_placing_and_removing_object(self):
        game_map = GameMap((16, 16), [])
        game_map[9, 6].place_object(object())
        game_map[9, 6].place_object(None)
        self.assertTrue(game_map[9, 6].empty)

    def test_cannot_change_position_of_field(self):
        game_map = GameMap((16, 16), [])
        def illegal_operation():
            game_map[6, 5] = game_map[7, 8]
        self.assertRaises(ValueError, illegal_operation)

    def test_getting_field_outside_map(self):
        game_map = GameMap((16, 16), ())

        field = game_map[-1, 0]

        self.assertEqual(field.ground_type, None) # None is default ground type
        self.assertEqual(field.valid_position, False)
        self.assertEqual(field.position, (-1, 0))
        self.assertEqual(field.maybe_object, None)
        self.assertEqual(field.accessible, False)
        self.assertEqual(field.empty, True)
        illegal_operation = lambda: field.change_ground(0)
        self.assertRaises(FieldOutsideMap, illegal_operation)
        illegal_operation = lambda: field.place_object(None)
        self.assertRaises(FieldOutsideMap, illegal_operation)
        illegal_operation = lambda: field.place_object(object())
        self.assertRaises(FieldOutsideMap, illegal_operation)

    def test_finding_accessible_neighbour_when_it_doesnt_exist(self):
        game_map = self._create_game_map(occupied_positions=[(0, 1), (1, 0)])
        answer = game_map.find_accessible_neighbour_of((0, 0))
        self.assertEqual(answer, None)

    def test_finding_accessible_neighbour_when_it_exists(self):
        game_map = self._create_game_map(occupied_positions=[(0, 1)])
        answer = game_map.find_accessible_neighbour_of((0, 0))
        self.assertEqual(answer.position, (1, 0))

    def test_reserving_start_position_when_its_occupied(self):
        game_map = self._create_game_map(start_positions=[(8, 8)],
                                         occupied_positions=[(8, 8)])
        self.assertEqual(game_map.try_reserve_free_start_position(), None)

    def test_reserving_start_position_when_its_neighbour_is_occupied(self):
        game_map = self._create_game_map(start_positions=[(8, 8)],
                                         occupied_positions=[(8, 7)])
        self.assertEqual(game_map.try_reserve_free_start_position(), None)

    def test_reserving_start_position_when_its_not_occupied(self):
        game_map = self._create_game_map(start_positions=[(8, 8)],
                                         occupied_positions=[(7, 7)])
        self.assertEqual(game_map.try_reserve_free_start_position(), (8, 8))

    def test_reserving_start_position_when_there_are_more_then_one(self):
        free_start_position = (9, 9)
        game_map = self._create_game_map(
            start_positions=\
                [(1, 8), (3, 8), (5, 8), (7, 8), free_start_position],
            occupied_positions=\
                [(1, 9), (3, 9), (5, 9), (7, 9)])
        self.assertEqual(game_map.try_reserve_free_start_position(),
                         free_start_position)

    def test_reserving_start_position_when_its_on_edge(self):
        game_map = self._create_game_map(start_positions=[(0, 8)])
        self.assertEqual(game_map.try_reserve_free_start_position(), None)

    def test_deepcopying_correctness(self):
        start_positions = [(3, 3), (4, 5)]
        original = GameMap((128, 128), start_positions)
        copied = copy.deepcopy(original)

        # check independence of objects on map
        position = (124, 124)
        original[position].place_object(object())
        self.assertEqual(copied[position].maybe_object, None)

        # check independence of _free_start_positions
        self.assertEqual(original._free_start_positions,
                         copied._free_start_positions)
        original.try_reserve_free_start_position()
        self.assertNotEqual(original._free_start_positions,
                            copied._free_start_positions)

    def test_repr_on_game_map(self):
        game_map = GameMap((16, 12), [(12, 6), (6, 3)])
        expected = "GameMap(16x12, id=0x%x)" % id(game_map)
        self.assertEqual(str(game_map), expected)

    def test_repr_on_field(self):
        game_map = GameMap((16, 12), [(12, 6), (6, 3)])
        field = game_map[12, 4]
        field.place_object('<object>')
        expected = ("Field(position=(12, 4), "
                    "valid_position=True, "
                    "ground_type=1, "
                    "maybe_object='<object>', "
                    "id(game_map)=0x%x)" % id(game_map))
        self.assertEqual(str(field), expected)

    def _create_game_map(self, start_positions=(), occupied_positions=()):
        game_map = GameMap((16, 16), start_positions)
        for occupied_position in occupied_positions:
            game_map[occupied_position].place_object(object())
        return game_map


class TestGameMapEfficiency(unittest.TestCase):
    @ max_time(25)
    def test_deepcopying(self):
        original = GameMap((128, 128), ())
        copied = copy.deepcopy(original)


class TestFindingPath(unittest.TestCase):
    def test_destination_equal_to_source(self):
        self.game_map = GameMap((4, 4), ())
        self.source = self.destination = (3, 2)
        self._test_answer_equal_to(None)

    def test_destination_is_source_neighbour(self):
        self.game_map = GameMap((4, 4), ())
        self.source = (3, 2)
        self.destination = (3, 3)
        self._test_answer_equal_to(direction.S)

    def test_destination_is_unavaiable_but_its_neighbour_is_not(self):
        s = 'tt    \n' + \
            'ttttt \n' + \
            '      \n' + \
            ' ttttt\n' + \
            ' t    \n' + \
            '   tt*'
        self.game_map = self._create_game_map_from_text(s)
        self.destination = (1, 0)
        self._test_answer_equal_to(direction.N)

    def test_destination_is_far_far_away_but_is_avaiable(self):
        size = 128
        self.game_map = GameMap((size, size), ())
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
        self._test_answer_equal_to(None)

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
        s = '*t'
        self.destination = (1, 0)
        self.game_map = self._create_game_map_from_text(s)
        self._test_answer_equal_to(None)

    def test_destination_behind_border(self):
        self.game_map = GameMap((3, 3), ())
        self.destination = (3, 0)
        self.source = (2, 0)
        self._test_answer_equal_to(None)

    def test_skip_if_too_long_searching_time(self):
        assert _FindPathProblem.ITERATIONS_LIMIT == 256
        s = ' '*257
        self.game_map = self._create_game_map_from_text(s)
        self.source = (0, 0)
        self.destination = (256, 0)
        self._test_answer_equal_to(None)

    def _create_game_map_from_text(self, s):
        """ '*' means source and '^' - destination """

        split = s.split('\n')

        size_x, size_y = len(split[0]), len(split)

        game_map = GameMap((size_x, size_y), ())

        switch = {
            ' ': lambda field: None,
            't': lambda field: field.place_object(object()),
            '*': lambda field: setattr(self, 'source', field.position),
            '^': lambda field: setattr(self, 'destination', field.position),
        }
        for y, line in enumerate(split):
            for x, char in enumerate(line):
                case = switch[char]
                case(game_map[x, y])

        return game_map

    def _test_answer_equal_to(self, expected_direction):
        answered_direction = self._find_direction()
        self.assertEqual(expected_direction, answered_direction)

    def _find_direction(self):
        return self.game_map.find_direction(self.source, self.destination)


class TestFindingPathEfficiency(unittest.TestCase):
    @ max_time(10)
    def test_efficiency_on_blank_map_with_non_heura_algorythm(self):
        size_of_map = _FindPathProblem.MIN_DISTANCE_TO_USE_HEURA/2-1
        assert (distance(self.source, self.destination) < \
                _FindPathProblem.MIN_DISTANCE_TO_USE_HEURA)
        self._test_efficiency_on_blank_map(size_of_map)

    @ max_time(150)
    def test_efficiency_on_blank_map_with_heura_algorythm(self):
        size_of_map = 128
        assert (distance(self.source, self.destination) >= \
                FindPathProblem.MIN_DISTANCE_TO_USE_HEURA)
        self._test_efficiency_on_blank_map(size_of_map)

    def _test_efficiency_on_blank_map(self, size_of_map):
        self.game_map = GameMap((size_of_map, size_of_map))
        self.source = size_of_map-1, 0
        self.destination = 0, size_of_map-1
        answered_direction = self._find_direction()
        self.assertTrue(answered_direction != None)

    def _find_direction(self):
        return self.game_map.find_direction(self.source, self.destination)

