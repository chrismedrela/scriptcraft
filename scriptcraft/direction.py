#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Define directions:
N
E
W
S

and dictionaries TO_RAY, FROM_RAY and BY_NAME.

"""


N, E, S, W = 'n', 'e', 's', 'w'

TO_RAY = {
	N : (0,-1),
	E : (1,0),
	S : (0,1),
	W : (-1,0),
}

FROM_RAY = {
	(0,-1) : N,
	(1,0) : E,
	(0,1) : S,
	(-1,0) : W,
}

BY_NAME = {
	'N':N, 'n':N,
	'E':E, 'e':E,
	'S':S, 's':S,
	'W':W, 'w':W,
}

TO_FULL_NAME = {
	N:'north',
	W:'west',
	S:'south',
	E:'east',
}

def estimated(source, dest):
    dx, dy = dest[0]-source[0], dest[1]-source[1]
    if dx==dy==0:
        return None
    if abs(dx) > abs(dy): # then estimated direction is W or E
        return E if dx > 0 else W
    else: # then estimated direction is S or N
        return S if dy > 0 else N

