
import unittest

from scriptcraft.core import direction
from scriptcraft.core.FindPathProblem import FindPathProblem
from scriptcraft.core.GameMap import GameMap
from scriptcraft.utils import *



class TestFindingPath(unittest.TestCase):

    def test_destination_equal_to_source(self):
        s = '    \n' + \
            '    \n' + \
            '    \n' + \
            '    '
        self.game_map = self._create_game_map_from_text(s)

        self.source = self.destination = (3, 2)
        excepted_direction = None
        self._test_answer_equal_to(excepted_direction)


    def test_destination_is_source_neightbour(self):
        s = '    \n' + \
            '    \n' + \
            '   *\n' + \
            '   ^'
        self.game_map = self._create_game_map_from_text(s)

        excepted_direction = direction.S
        self._test_answer_equal_to(excepted_direction)


    def test_destination_is_unavaiable_but_its_neightbour_is_not(self):
        s = 'tu    \n' + \
            'ttttt \n' + \
            '      \n' + \
            ' ttttt\n' + \
            ' t    \n' + \
            '   tt*'
        self.game_map = self._create_game_map_from_text(s)

        self.destination = (1, 0)
        excepted_direction = direction.N
        self._test_answer_equal_to(excepted_direction)


    def test_destination_is_far_far_away_but_is_avaiable(self):
        size = 128
        self.game_map = GameMap((size, size))
        self.source = 14, 0
        self.destination = 14+size/2, size-1

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction in (direction.E, direction.S))


    def test_destination_is_unavailable_nor_its_neightbours(self):
        s = ' t  \n' + \
            ' t  \n' + \
            '*t  \n' + \
            ' t^ '
        self.game_map = self._create_game_map_from_text(s)

        excepted_direction = None
        self._test_answer_equal_to(excepted_direction)


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


    @ max_time(10)
    def test_efficiency_on_blank_map_with_non_heura_algorythm(self):
        size = FindPathProblem.MIN_DISTANCE_TO_USE_HEURA/2-1
        self.game_map = GameMap((size, size))
        self.source = size-1, 0
        self.destination = 0, size-1

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction != None)

        assert distance(self.source, self.destination) < FindPathProblem.MIN_DISTANCE_TO_USE_HEURA


    @ max_time(150)
    def test_efficiency_on_blank_map_with_heura_algorythm(self):
        size = 128
        self.game_map = GameMap((size, size))
        self.source = 0, 0
        self.destination = size-1, size-1

        answered_direction = self._find_direction()
        self.assertTrue(answered_direction != None)

        assert distance(self.source, self.destination) >= FindPathProblem.MIN_DISTANCE_TO_USE_HEURA


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


    def _test_answer_equal_to(self, excepted_direction):
        answered_direction = self._find_direction()
        self.assertEqual(excepted_direction, answered_direction)


    def _find_direction(self):
        problem = FindPathProblem(self.source, self.destination, self.game_map)
        answer = problem.find_direction()
        return answer

