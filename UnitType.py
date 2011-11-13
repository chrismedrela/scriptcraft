#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from utils import *



BEHAVIOUR_WHEN_ATTACKED = make_enum("BEHAVIOUR_WHEN_ATTACKED",
                                    "DESTROY GET_MINERAL_OR_DESTROY")

class UnitType(namedtuple('UnitType', ('attack_range',
                                       'vision_range',
                                       'store_size',
                                       'cost_of_build',
                                       'can_build',
                                       'movable',
                                       'behaviour_when_attacked',
                                       'names'))):
    """
    Attributes:
    attack_range -- value 0 means unit cannot attack
    vision_range -- 0 is valid value
    store_size -- value 0 means unit cannot store minerals; value -1 means
        there is no limit
    cost_of_build -- value -1 means unit cannot be built
        and 0 is valid value
    can_build
    movable
    behaviour_when_attacked -- enum BEHAVIOUR_WHEN_ATTACKED
    names -- list or tuple

    """

    __slots__ = ()
