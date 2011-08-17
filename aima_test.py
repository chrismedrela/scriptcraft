#!/usr/bin/env python
#-*- coding:utf-8 -*-

import aima.search as ai

class MyProblem(ai.Problem):
    """The abstract class for a formal problem.  You should subclass this and
    implement the method successor, and possibly __init__, goal_test, and
    path_cost. Then you will create instances of your subclass and solve them
    with the various search functions."""

    def __init__(self, initial, goal, mapa, size):
        """The constructor specifies the initial state, and possibly a goal
        state, if there is a unique goal.  Your subclass's constructor can add
        other arguments."""
        self.initial = initial
        self.goal = goal
        self.mapa = mapa
        self.size = size

    def successor(self, state):
        """Given a state, return a sequence of (action, state) pairs reachable
        from this state. If there are many successors, consider an iterator
        that yields the successors one at a time, rather than building them
        all at once. Iterators will work fine within the framework."""
        x, y = state
        s = []
        if x>0 and mapa[x-1][y]!=-2: s.append( (None, (x-1,y)) )
        if y>0 and mapa[x][y-1]!=-2: s.append( (None, (x,y-1)) )
        if x<self.size-1 and mapa[x+1][y]!=-2: s.append( (None, (x+1,y)) )
        if y<self.size-1 and mapa[x][y+1]!=-2: s.append( (None, (x,y+1)) )
       	return s

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal, as specified in the constructor. Implement this
        method if checking against a single self.goal is not enough."""
        return state == self.goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def value(self):
        """For optimization problems, each state has a value.  Hill-climbing
        and related algorithms try to maximize this value."""
        abstract
        
    def h(self, node):
    	x, y = node.state
    	return abs(x-self.goal[0]) + abs(y-self.goal[1])

        
if __name__ == "__main__":
	size = 8
	mapa = [[-1 for y in xrange(size)] for x in xrange(size)]
	mapa[4][2] = mapa[4][3] = mapa[4][4] = mapa[3][4] = mapa[2][4] = mapa[1][4] = -2
	mapa[6][6] = -2
	problem = MyProblem((1,1), (6,6), mapa, size)

	result = ai.astar_search(problem)

	print result
	licznik = 0
	while result != None:
		print result
		x, y = result.state
		mapa[x][y] = licznik
		licznik += 1
		result = result.parent
		
	for y in xrange(size):
		for x in xrange(size):
			print ("%d"%mapa[x][y] if mapa[x][y]>=0 else "x" if mapa[x][y]==-2 else '.').center(2), 
		print ""		
		
	
