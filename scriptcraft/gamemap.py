#!/usr/bin/env python
#-*- coding:utf-8 -*-

from copy import deepcopy

from scriptcraft import aima, direction
from scriptcraft.utils import *



class FieldOutsideMap(Exception):
    pass

class FieldIsOccupied(Exception):
    pass


class GameMap(object):
    DEFAULT_GROUND_TYPE = 1
    INVALID_GROUND_TYPE = None
    MIN_GROUND_TYPE = 1
    MAX_GROUND_TYPE = 127

    def __init__(self, size=None, start_positions=None, raw_instance=False):
        if raw_instance:
            return

        assert size[0]>0 and size[1]>0, \
            "map size must be at least 1x1"
        assert all(0 <= pos[0] < size[0] and 0 <= pos[1] < size[1]
                   for pos in start_positions), \
            "all start positions must be inside map"

        self._free_start_positions = set(start_positions)
        self._size = size

        # self._ground_types is dict {(x, y) : ground_type}
        self._ground_types = dict(((x, y), GameMap.DEFAULT_GROUND_TYPE)
                                  for x in xrange(size[0])
                                  for y in xrange(size[1]))
        # self._objs is dict {(x, y) : object on that field}
        self._objs = {}

    def __getitem__(self, position):
        valid_position = self._is_valid_position(position)
        if valid_position:
            ground_type = self._ground_types[position]
            obj = self._objs.get(position, None)
        else:
            ground_type, obj = GameMap.INVALID_GROUND_TYPE, None

        return Field(position, valid_position,
                     ground_type, obj, game_map=self)

    def __setitem__(self, position, field):
        if not self._is_valid_position(position):
            raise FieldOutsideMap('The position is outside map.')
        if field.position != position:
            raise ValueError('The field position was %r but you want assign '
                             'the field to %r.' % (field.position, position))
        old_ground_type = self._ground_types[position]
        old_obj = self._objs.get(position, None)
        if (old_obj is not None and
            field.maybe_object is not None and
            old_obj is not field.maybe_object):
            raise FieldIsOccupied('Cannot place object on occupied field. '
                                  'First remove the object.')
        assert (GameMap.MIN_GROUND_TYPE <=
                field.ground_type <=
                GameMap.MAX_GROUND_TYPE), \
            ('Invalid ground type. Ground type must be integer '
             'between %r and %r' % (GameMap.MIN_GROUND_TYPE,
                                    GameMap.MAX_GROUND_TYPE))
        self._ground_types[position] = field.ground_type
        if field.maybe_object is None:
            if position in self._objs:
                del self._objs[position]
        else:
            self._objs[position] = field.maybe_object

    def __deepcopy__(self, memo):
        result = GameMap(raw_instance=True)
        result._free_start_positions = deepcopy(self._free_start_positions, memo)
        result._size = deepcopy(self._size, memo)
        def copied_objs():
            for pos, obj in self._objs.iteritems():
                key = id(obj)
                if key not in memo:
                    memo[key] = deepcopy(obj, memo)
                yield (pos, memo[key])
        result._objs = dict(copied_objs())
        # self._ground_types are ints so we don't need to do deep copy
        result._ground_types = self._ground_types.copy()
        return result

    def __repr__(self):
        return "GameMap(%dx%d, id=0x%x)" % \
          (self._size[0], self._size[1], id(self))

    @property
    def size(self):
        return self._size

    def try_reserve_free_start_position(self):
        for position in self._free_start_positions:
            all_neighbours_are_accessible = all(
                neighbour.accessible for neighbour
                in self._get_four_neighbours_of(position)
            )
            if self[position].accessible and all_neighbours_are_accessible:
                self._free_start_positions.remove(position)
                return position
        return None

    def find_accessible_neighbour_of(self, position):
        for neighbour in self._get_four_neighbours_of(position):
            if neighbour.accessible:
                return neighbour
        return None

    def find_direction(self, source, destination):
        problem = _FindPathProblem(source, destination, self)
        return problem.find_direction()

    def _get_four_neighbours_of(self, pos):
        return (self[pos[0]-1, pos[1]],
                self[pos[0]+1, pos[1]],
                self[pos[0], pos[1]-1],
                self[pos[0], pos[1]+1])

    def _is_valid_position(self, position):
        return (0 <= position[0] < self._size[0] and
                0 <= position[1] < self._size[1])


class Field(object):
    __slots__ = ('_maybe_object',
                 '_valid_position',
                 '_position',
                 '_ground_type',
                 '_game_map')

    def __init__(self, position, valid_position,
                 ground_type, maybe_object, game_map):
        self._position = position
        self._valid_position = valid_position
        self._ground_type = ground_type
        self._maybe_object = maybe_object
        self._game_map = game_map

    def __eq__(self, other):
        return (type(self) == type(other) and
                self._game_map is other._game_map and
                all(getattr(self, attr) == getattr(other, attr)
                    for attr in ('_maybe_object', '_valid_position',
                                 '_position', '_ground_type')))

    def __repr__(self):
        return ("Field(position=%r, valid_position=%r, ground_type=%r, "
                "maybe_object=%r, id(game_map)=0x%x)" % \
                (self._position, self._valid_position, self._ground_type,
                 self._maybe_object, id(self._game_map)))

    @property
    def position(self):
        return self._position

    @property
    def valid_position(self):
        return self._valid_position

    @property
    def ground_type(self):
        return self._ground_type

    @property
    def maybe_object(self):
        return self._maybe_object

    @property
    def empty(self):
        return self._maybe_object is None

    @property
    def accessible(self):
        return self._maybe_object is None and self._valid_position

    def change_ground(self, new_ground):
        self._ground_type = new_ground
        self._game_map[self._position] = self

    def place_object(self, obj):
        self._maybe_object = obj
        self._game_map[self._position] = self


class _TooLongSearchingTime(Exception):
    pass


class _FindPathProblem(aima.search.Problem):
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
        self.h_coefficient = (_FindPathProblem.H_COEFFICIENT_FOR_NON_HEURA
                              if dist < _FindPathProblem.MIN_DISTANCE_TO_USE_HEURA
                              else _FindPathProblem.H_COEFFICIENT_FOR_HEURA)
        self.iteration = 0

    def successor(self, state):
        self.iteration += 1
        if self.iteration >= _FindPathProblem.ITERATIONS_LIMIT:
            raise _TooLongSearchingTime()

        x, y = state
        neighbour_positions = ((x - 1, y),
                               (x, y - 1),
                               (x + 1, y),
                               (x, y + 1))
        neighbours = [(None, position) for position in neighbour_positions
                      if (self.game_map[position].accessible
                          or position == self.destination)]
        return neighbours

    def goal_test(self, state):
        return state == self.destination

    def path_cost(self, c, state1, action, state2):
        return c + 1

    def h(self, node):
        x, y = node.state
        return distance((x, y), self.destination) * self.h_coefficient

    @log_on_enter('find path', mode='only time')
    def find_direction(self):
        """ Return None if start_position==destination or if destination
        is unavailable or if computing path took too long time. """

        if self.start_position == self.destination:
            return None

        try:
            result_node = aima.search.astar_search(self)
        except _TooLongSearchingTime:
            return None

        if result_node == None: # no path found
            return None

        path = result_node.path()
        first_node, second_node = path[-1], path[-2]
        delta = (second_node.state[0] - first_node.state[0],
                 second_node.state[1] - first_node.state[1])
        next_field = second_node.state

        if self.game_map[next_field].accessible:
            return direction.FROM_RAY[delta]
        else:
            return None



# ==============================================================================
# old code
# ==============================================================================

"""
from collections import namedtuple
import copy

from scriptcraft import aima
from scriptcraft import direction
from scriptcraft.utils import *



class NoFreeStartPosition(Exception):
    pass


class FieldIsOccupied(Exception):
    pass


class PositionOutOfMap(Exception):
    pass


class TooLongSearchingTime(Exception):
    pass


class GameMap(list):
    def __init__(self, size, start_positions=()):
        "Create rectangular, flat, empty map.

        Arguments:
        size -- tuple (x, y)
        start_positions -- sequence of start positions; every valid position is
            valid start position (for example (0,0) is OK, but (-1, 0) not)

        "

        x_size, y_size = size

        assert all(map(lambda (x,y): 0<=x<x_size and 0<=y<y_size, start_positions))

        start_positions = list(start_positions)

        super(GameMap, self).__init__(  [[Field() for y in xrange(y_size)] for x in xrange(x_size)]  )

        self._free_start_positions = start_positions
        self.size = size

    def reserve_next_free_start_position(self):
        "
        For any free start position all following conditions are truth:
         - the start position and its four neighbours exist and are empty and flat

        Each call return other start position or raise NoFreeStartPosition.
        "

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

    def find_flat_and_free_neighbour_of(self, position):
        x, y = position
        neighbours = ((x-1, y),
                      (x, y-1),
                      (x+1, y),
                      (x, y+1))

        for candidate in neighbours:
            if (self.is_valid_position(candidate)
                and self.get_field(candidate).is_flat_and_empty()):
                return candidate

        return None

    def get_field(self, position):
        x, y = position
        if x<0 or y<0 or x>=self.size[0] or y>=self.size[1]:
            raise PositionOutOfMap()

        return self[position[0]][position[1]]

    def is_valid_position(self, (x, y)):
        return x >= 0 and y >= 0 and x < self.size[0] and y < self.size[1]

    def is_valid_and_accessible(self, position):
        return (self.is_valid_position(position)
                and self.get_field(position).is_flat_and_empty())

    def place_trees_at(self, position):
        function = lambda field: field.PlacedTrees()
        self._change_field_with_function_if_empty(position, function)

    def place_minerals_at(self, position, minerals):
        function = lambda field: field.PlacedMinerals(minerals)
        self._change_field_with_function_if_empty(position, function)

    def place_unit_at(self, position, unit):
        function = lambda field: field.PlacedUnit(unit)
        self._change_field_with_function_if_empty(position, function)

    def erase_at(self, position):
        function = lambda field: field.Erased()
        self._change_field_with_function(position, function)

    def find_direction(self, source, destination):
        problem = _FindPathProblem(source, destination, self)
        return problem.find_direction()

    def _change_field_with_function_if_empty(self, position, function):
        if not self[position[0]][position[1]].is_empty():
            raise FieldIsOccupied()
        self._change_field_with_function(position, function)

    def _change_field_with_function(self, position, function):
        field = self[position[0]][position[1]]
        field = function(field)
        self[position[0]][position[1]] = field

    @log_on_enter('copying map', mode='only time')
    def __deepcopy__(self, memo):
        c = copy.copy(self)

        for i in xrange(self.size[0]):
            c[i] = self[i][:]

        c._free_start_positions = self._free_start_positions[:]

        return c


class Field():
    "
    A field can has:
     mineral deposit (keyworded argument: minerals : int = number of minerals in deposit)
     *xor* trees (keyworded argument: trees : bool)
     *xor* unit (keyworded argument: unit : any object)

    Do *not* use attributes 'type' and 'arg'. Instead use methods.

    Implementation:
     type -- describe shape of field (flat, upland)
     arg -- describe object *on* a field:
        arg == 0 <==> nothing on a field
        arg is not int <==> unit on field; arg is the unit
        arg == -1 <==> trees
        arg <= -2 <==> minerals; -(arg+2) is number of minerals

    Examples:
    >>> Field(upland=True, minerals=0)
    <Field(type=2, arg=-2) : upland with 0 minerals>
    >>> Field(unit='my unit')
    <Field(type=1, arg='my unit') : flat field with unit 'my unit'>
    >>> Field(trees=True)
    <Field(type=1, arg=-1) : flat field with trees>
    >>> Field(minerals=2, unit=object())
    ...
    ValueError: Field can not has more than one of: mineral deposit, tree and unit
    >>> f = Field(upland=True, minerals=2)
    >>> f.Erased()
    <Field(type=2, arg=0) : empty upland>
    >>> f.PlacedUnit('unit')
    <Field(type=2, arg='unit') : upland with unit 'unit'>

    "

    __metaclass__ = record
    _fields = ('type', 'arg')

    def __new__(cls, upland=False, minerals=None, unit=None, trees=False):
        type = 2 if upland else 1

        if sum( ((minerals!=None), (unit!=None), (trees)) ) > 1:
            raise ValueError('Field can not has more than one of: mineral deposit, tree and unit')
        arg = 0
        if trees:
            arg = -1
        elif minerals != None:
            arg = -minerals-2
        elif unit != None:
            arg = unit

        return cls.__bases__[0].__new__(cls, type, arg)

    def is_flat(self):
        return self.type == 1

    def is_upland(self):
        return self.type == 2

    def is_empty(self):
        return self.arg == 0

    def is_flat_and_empty(self):
        return self.type == 1 and self.arg == 0

    def has_trees(self):
        return self.arg == -1

    def has_mineral_deposit(self):
        return self.arg <= -2

    def has_unit(self):
        return not isinstance(self.arg, int)

    def get_minerals(self):
        assert self.arg <= -2
        return -(self.arg+2)

    def get_unit(self):
        return self.arg

    def PlacedTrees(self):
        return self._replace(arg=-1)

    def PlacedMinerals(self, how_much):
        return self._replace(arg=-2-how_much)

    def PlacedUnit(self, unit):
        return self._replace(arg=unit)

    def Erased(self):
        return self._replace(arg=0)

    def __str__(self):
        return "<{empty}{shape}{obj}>".format(
            empty = 'empty ' if self.is_empty() else '',
            shape = 'upland' if self.is_upland() else 'flat field',
            obj = '' if self.is_empty() else \
                ' with trees' if self.has_trees() else \
                ' with {0} minerals'.format(self.get_minerals()) if self.has_mineral_deposit() else \
                ' with unit {0}'.format(str(self.get_unit()))
        )

    def __repr__(self):
        return ('<' +
                super(Field, self).__repr__() +
                ' : ' +
                str(self)[1:-1] +
                '>')


class _FindPathProblem(aima.search.Problem):
    "
    Represent problem of finding path in scriptcraft.core.GameMap
    to an field *or one of its neightbours*.

    Using:
    >>> problem = _FindPathProblem(start_position, destination, game_map)
    >>> maybe_direction = problem.find_direction()
    "

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
        self.h_coefficient = (_FindPathProblem.H_COEFFICIENT_FOR_NON_HEURA
                              if dist < _FindPathProblem.MIN_DISTANCE_TO_USE_HEURA
                              else _FindPathProblem.H_COEFFICIENT_FOR_HEURA)
        self.iteration = 0

    def successor(self, state):
        self.iteration += 1
        if self.iteration >= _FindPathProblem.ITERATIONS_LIMIT:
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

    @log_on_enter('find path', mode='only time')
    def find_direction(self):
        " Return None if start_position==destination or if destination
        is unavailable or if computing path took too long time. "

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

"""
