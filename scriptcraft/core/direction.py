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
	'N' : N,
	'E' : E,
	'S' : S,
	'W' : W,
}
