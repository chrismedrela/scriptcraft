#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from scriptcraft.utils import *



BEHAVIOUR_WHEN_ATTACKED = make_enum("BEHAVIOUR_WHEN_ATTACKED",
                                    "DESTROY GET_MINERAL_OR_DESTROY")

class UnitType(namedtuple('UnitType', ('attack_range',
                                       'vision_radius',
                                       'storage_size',
                                       'build_cost',
                                       'can_build',
                                       'movable',
                                       'behaviour_when_attacked',
                                       'names'))):
    """
    Attributes:
    attack_range -- value 0 means unit cannot attack
    can_attack -- if False then attack_range == 0
    vision_radius -- 0 is valid value
    vision_diameter -- computed from vision_radius; not allowed in __init__ args
    storage_size -- value -1 means there is no limit
    has_storage -- if False then store_size == 0
    build_cost -- 0 is valid value; it hasn't sense when buildable==False
    can_be_built -- if False then build_cost == -1
    can_build
    movable
    behaviour_when_attacked -- enum BEHAVIOUR_WHEN_ATTACKED
    names -- non-empty list or tuple (always lowercase)
    main_name -- the first name from names (always lowercase)

    """

    __slots__ = ()


    @ copy_if_an_instance_given
    def __new__(cls, **kwargs):
        if 'build_cost' in kwargs:
            assert kwargs['build_cost'] >= 0
            assert kwargs.get('can_be_built', True)
        else:
            assert 'can_be_built' in kwargs and kwargs['can_be_built'] == False
            del kwargs['can_be_built']
            kwargs['build_cost'] = -1

        if 'has_storage' in kwargs:
            if not kwargs['has_storage']:
                assert kwargs.get('storage_size', 0) == 0
                kwargs['storage_size'] = 0
            else:
                assert 'storage_size' in kwargs
            del kwargs['has_storage']

        if 'can_attack' in kwargs:
            if not kwargs['can_attack']:
                assert kwargs.get('attack_range', 0) == 0
                kwargs['attack_range'] = 0
            else:
                assert 'attack_range' in kwargs
            del kwargs['can_attack']

        kwargs['names'] = map(lambda x: x.lower(),
                              kwargs['names'])

        return cls.__bases__[0].__new__(cls, **kwargs)


    def __deepcopy__(self, memo):
        c = UnitType(self)
        return c


    @ property
    def main_name(self):
        return self.names[0]


    @ property
    def vision_diameter(self):
        return 2*self.vision_radius + 1


    @ property
    def can_be_built(self):
        return self.build_cost != -1


    @ property
    def has_storage(self):
        return self.storage_size != 0


    @ property
    def has_storage_limit(self):
        return self.storage_size != -1


    @ property
    def can_attack(self):
        return self.attack_range != 0

