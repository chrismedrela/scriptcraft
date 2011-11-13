#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy

from Field import Field



class NoFreeStartPosition(Exception):
    pass

class CannotPlaceOnOccupedField(Exception):
    pass


class GameMap(list):

    def __init__(self, size, start_positions=()):
        """Create rectangular, flat, empty map.

        Arguments:
        size -- tuple (x, y)
        start_positions -- sequence of start positions; every valid position is
            valid start position (for example (0,0) is OK, but (-1, 0) not)

        """

        x_size, y_size = size

        assert all(map(lambda (x,y): 0<=x<x_size and 0<=y<y_size, start_positions))

        start_positions = list(start_positions)

        super(GameMap, self).__init__(  [[Field() for y in xrange(y_size)] for x in xrange(x_size)]  )

        self._free_start_positions = start_positions
        self.size = size




    def reserve_next_free_start_position(self):
        """
        For any free start position all following conditions are truth:
         - the start position and its four neighbours exist and are empty and flat

        Each call return other start position or raise NoFreeStartPosition.
        """

        for candidate in self._free_start_positions:
            if self._is_free_position(candidate):
                self._free_start_positions.remove(candidate)
                return candidate

        raise NoFreeStartPosition()

    def _is_free_position(self, position):
        x, y = position

        if self._is_position_on_border(position):
            return False

        position_and_neighbours = [self[x][y], self[x-1][y], self[x+1][y], self[x][y-1], self[x][y+1]]
        for field in position_and_neighbours:
            if not field.is_empty() or not field.is_flat():
                return False

        return True

    def _is_position_on_border(self, position):
        x, y = position
        return x==0 or x==self.size[0]-1 or y==0 or y==self.size[1]-1


    def place_trees_at(self, position):
        function = lambda field: field.PlacedTrees()
        self._change_field_with_function_if_empty(position, function)

    def place_minerals_at(self, position, minerals):
        function = lambda field: field.PlacedMinerals(minerals)
        self._change_field_with_function_if_empty(position, function)

    def place_unit_at(self, position, unit_ID):
        function = lambda field: field.PlacedUnit(unit_ID)
        self._change_field_with_function_if_empty(position, function)

    def erase_at(self, position):
        function = lambda field: field.Erased()
        self._change_field_with_function(position, function)

    def _change_field_with_function_if_empty(self, position, function):
        if not self[position[0]][position[1]].is_empty():
            raise CannotPlaceOnOccupedField()
        self._change_field_with_function(position, function)

    def _change_field_with_function(self, position, function):
        field = self[position[0]][position[1]]
        field = function(field)
        self[position[0]][position[1]] = field

    def __deepcopy__(self, memo):
        c = copy.copy(self)

        for i in xrange(self.size[0]):
            c[i] = self[i][:]

        c._free_start_positions = self._free_start_positions[:]

        return c