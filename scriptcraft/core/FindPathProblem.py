#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft import aima
from scriptcraft.core import direction
from scriptcraft.utils import *



class TooLongSearchingTime(Exception):
    pass


class FindPathProblem(aima.search.Problem):
    """
    Represent problem of finding path in scriptcraft.core.GameMap
    to an field *or one of its neightbours*.

    Using:
    >>> problem = FindPathProblem(start_position, destination, game_map)
    >>> maybe_direction = problem.find_direction()
    """

    ITERATIONS_LIMIT = 256
    MIN_DISTANCE_TO_USE_HEURA = 16
    H_COEFFICIENT_FOR_NON_HEURA = 1.0
    H_COEFFICIENT_FOR_HEURA = 1.03

    def __init__(self, start_position, destination, game_map):
        aima.search.Problem.__init__(self, start_position, destination)
        self.start_position = start_position
        self.destination = destination
        self.game_map = game_map
        dist = distance(start_position, destination)
        self.h_coefficient = (FindPathProblem.H_COEFFICIENT_FOR_NON_HEURA
                              if dist < FindPathProblem.MIN_DISTANCE_TO_USE_HEURA
                              else FindPathProblem.H_COEFFICIENT_FOR_HEURA)
        self.iteration = 0

    def successor(self, state):
        self.iteration += 1
        if self.iteration >= FindPathProblem.ITERATIONS_LIMIT:
            raise TooLongSearchingTime()

        x, y = state
        neighbour_positions = ((x - 1, y),
                               (x, y - 1),
                               (x + 1, y),
                               (x, y + 1))
        neighbours = [(None, position) for position in neighbour_positions
                      if (self.game_map.is_valid_and_accessible(position)
                          or position == self.destination)]
        return neighbours

    def goal_test(self, state):
        return state == self.destination

    def path_cost(self, c, state1, action, state2):
        return c + 1

    def h(self, node):
        x, y = node.state
        return distance((x, y), self.destination) * self.h_coefficient

    def find_direction(self):
        """ Return None if start_position==destination or if destination
        is unavailable or if computing path took too long time. """

        if self.start_position == self.destination:
            return None

        try:
            result_node = aima.search.astar_search(self)
        except TooLongSearchingTime:
            return None

        if result_node == None: # no path found
            return None

        path = result_node.path()
        first_node, second_node = path[-1], path[-2]
        delta = (second_node.state[0] - first_node.state[0],
                 second_node.state[1] - first_node.state[1])
        next_field = second_node.state

        if self.game_map.is_valid_and_accessible(next_field):
            return direction.FROM_RAY[delta]
        else:
            return None
