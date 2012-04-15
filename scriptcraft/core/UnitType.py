#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from scriptcraft.utils import *



class BEHAVIOUR_WHEN_ATTACKED(object):
    DESTROY = '<Enum: destroy>'
    GET_MINERAL_OR_DESTROY = '<Enum: get mineral or destroy>'

#BEHAVIOUR_WHEN_ATTACKED = make_enum("BEHAVIOUR_WHEN_ATTACKED",
#                                "DESTROY GET_MINERAL_OR_DESTROY")


def _use_default_value_if_flag_is_False(kwargs, flag_name, attribute_name, default_value):
    if flag_name in kwargs:
        if not kwargs[flag_name]:
            assert kwargs.get(attribute_name, default_value) == default_value
            kwargs[attribute_name] = default_value
        else:
            assert attribute_name in kwargs
        del kwargs[flag_name]


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
    names -- non-empty list or tuple (always lowercase); the first name is main name
    main_name -- not allowed in __init__ args - it's the first name from names

    """

    __slots__ = ()

    @ copy_if_an_instance_given
    def __new__(cls, **kwargs):
        _use_default_value_if_flag_is_False(kwargs, 'can_be_built', 'build_cost', -1)
        _use_default_value_if_flag_is_False(kwargs, 'has_storage', 'storage_size', 0)
        _use_default_value_if_flag_is_False(kwargs, 'can_attack', 'attack_range', 0)

        if len(kwargs['names']) == 0:
            raise ValueError('unit type must have at least one name')

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


DEFAULT_MINER_TYPE = UnitType(
    attack_range=0,
    vision_radius=7,
    storage_size=1,
    build_cost=3,
    can_build=False,
    movable=True,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
    names=('5', 'miner', 'm')
)
DEFAULT_BASE_TYPE = UnitType(
    attack_range=0,
    vision_radius=16,
    has_storage=True,
    storage_size= -1,
    can_be_built=False,
    can_build=True,
    movable=False,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY,
    names=('4', 'base', 'b')
)
DEFAULT_TANK_TYPE = UnitType(
    can_attack=True,
    attack_range=3,
    vision_radius=7,
    has_storage=False,
    build_cost=10,
    can_build=False,
    movable=True,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
    names=('6', 'tank', 't')
)
