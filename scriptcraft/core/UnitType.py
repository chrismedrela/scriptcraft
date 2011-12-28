#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from scriptcraft.utils import *



BEHAVIOUR_WHEN_ATTACKED = make_enum("BEHAVIOUR_WHEN_ATTACKED",
                                    "DESTROY GET_MINERAL_OR_DESTROY")

class UnitType(namedtuple('UnitType', ('attack_range',
                                       'vision_radius',
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
    can_be_built -- if False then cost_of_build == -1
    cost_of_build -- 0 is valid value; it hasn't sense when buildable==False
    can_build
    movable
    behaviour_when_attacked -- enum BEHAVIOUR_WHEN_ATTACKED
    names -- non-empty list or tuple
    main_name -- the first name from names

    """

    __slots__ = ()


    def __new__(cls, **kwargs):
        if 'cost_of_build' in kwargs:
            assert kwargs['cost_of_build'] >= 0
            assert kwargs.get('can_be_built', True)
        else:
            assert 'can_be_built' in kwargs and kwargs['can_be_built'] == False
            del kwargs['can_be_built']
            kwargs['cost_of_build'] = -1

        return cls.__bases__[0].__new__(cls, **kwargs)


    @ property
    def main_name(self):
        return self.names[0]


    @ property
    def vision_diameter(self):
        return 2*self.vision_radius + 1


    @ property
    def can_be_built(self):
        return self.cost_of_build == -1
