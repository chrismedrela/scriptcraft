import aima

from scriptcraft.core import direction
from scriptcraft.utils import *



class TooLongSearchingTime(Exception):
    pass



class FindPathProblem(aima.search.Problem):
    """ Represent problem of finding path in scriptcraft.core.GameMap
    to an field *or one of its neightbours*.

    """

    ITERATIONS_LIMIT = 256
    MIN_DISTANCE_TO_USE_HEURA = 16
    H_COEFFICIENT_FOR_HEURA = 1.03


    def __init__(self, start_position, destination, game_map):
        aima.search.Problem.__init__(self, start_position, destination)
        self.start_position = start_position
        self.destination = destination
        self.game_map = game_map
        self.h_coefficient = (1
                              if distance(start_position, destination) < FindPathProblem.MIN_DISTANCE_TO_USE_HEURA
                              else FindPathProblem.H_COEFFICIENT_FOR_HEURA)
        self.iteration = 0


    def successor(self, state):
        self.iteration += 1
        if self.iteration >= FindPathProblem.ITERATIONS_LIMIT:
            raise TooLongSearchingTime()

        field_x, field_y = state
        neightbours = []
        game_map = self.game_map
        destination = self.destination

        is_valid_position = lambda (x, y): x >= 0 and y >= 0 and x < game_map.size[0] and y < game_map.size[1]
        is_valid_position_and_flat_and_empty = lambda (x, y): is_valid_position((x, y)) and game_map[x][y].is_empty() and game_map[x][y].is_flat()

        neightbour_positions = ((field_x - 1, field_y),
                                (field_x, field_y - 1),
                                (field_x + 1, field_y),
                                (field_x, field_y + 1))

        for x, y in neightbour_positions:
            if is_valid_position_and_flat_and_empty((x, y)) or (x, y) == destination:
                neightbours.append((None, (x, y)))

        return neightbours


    def goal_test(self, state):
        return state == self.destination


    def path_cost(self, c, state1, action, state2):
        return c + 1


    def h(self, node):
        x, y = node.state
        return distance((x, y), self.destination) * self.h_coefficient


    def find_direction(self):
        """ Return None if start_position==destination or if destination is unavailable. """

        if self.start_position == self.destination:
            return None

        try:
            result_node = aima.search.astar_search(self)
        except TooLongSearchingTime:
            return None

        if result_node == None: # no path found
            return None

        path = result_node.path()
        first_node = path[-1]
        second_node = path[-2]

        delta_x, delta_y = (second_node.state[0] - first_node.state[0],
                            second_node.state[1] - first_node.state[1])

        next_x, next_y = second_node.state

        if self.game_map[next_x][next_y].is_flat() and self.game_map[next_x][next_y].is_empty():
            return direction.FROM_RAY[(delta_x, delta_y)]
        else:
            return None
