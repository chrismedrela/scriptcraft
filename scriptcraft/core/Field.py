#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from scriptcraft.utils import *



class Field(namedtuple('Field', ('type', 'arg'))):
    """
    A field can has:
     mineral deposit (keyworded argument: minerals : int = number of minerals in deposit)
     *xor* trees (keyworded argument: trees : bool)
     *xor* unit (keyworded argument: unit_ID : int)

    Do *not* use attributes 'type' and 'arg'. Instead use methods.

    Implementation:
     type -- describe shape of field (flat, upland)
     arg -- describe object *on* a field:
        arg == 0 <==> nothing on a field
        arg > 0 <==> unit on field; arg is unit ID
        arg == -1 <==> trees
        arg <= -2 <==> minerals; -(arg+2) is number of minerals

    Examples:
    >>> Field(upland=True, minerals=0)
    <Field(type=2, arg=-2) : upland with 0 minerals>
    >>> Field(unit_ID=3)
    <Field(type=1, arg=3) : flat field with unit 3>
    >>> Field(trees=True)
    <Field(type=1, arg=-1) : flat field with trees>
    >>> Field(minerals=2, object_ID=1)
    ...
    ValueError: Field can not has more than one of: mineral deposit, tree and unit
    >>> f = Field(upland=True, minerals=2)
    >>> f.Erased()
    <Field(type=2, arg=0) : empty upland>
    >>> f.PlacedUnit(2)
    <Field(type=2, arg=2) : upland with unit 2>

    """

    __slots__ = ()

    @ copy_if_an_instance_given
    def __new__(cls, upland=False, minerals=None, unit_ID=None, trees=False):
        type = 2 if upland else 1

        if sum( ((minerals!=None), (unit_ID!=None), (trees)) ) > 1:
            raise ValueError('Field can not has more than one of: mineral deposit, tree and unit')
        arg = 0
        if trees:
            arg = -1
        elif minerals != None:
            arg = -minerals-2
        elif unit_ID != None:
            arg = unit_ID

        return cls.__bases__[0].__new__(cls, type, arg)

    def __deepcopy__(self, memo):
        c = Field(self)
        return c

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
        return self.arg > 0

    def get_minerals(self):
        assert self.arg <= -2
        return -(self.arg+2)

    def get_unit_ID(self):
        return self.arg

    def PlacedTrees(self):
        return self._replace(arg=-1)

    def PlacedMinerals(self, how_much):
        return self._replace(arg=-2-how_much)

    def PlacedUnit(self, unit_ID):
        return self._replace(arg=unit_ID)

    def Erased(self):
        return self._replace(arg=0)

    def __str__(self):
        return "<{empty}{shape}{obj}>".format(
            empty = 'empty ' if self.is_empty() else '',
            shape = 'upland' if self.is_upland() else 'flat field',
            obj = '' if self.is_empty() else \
                ' with trees' if self.has_trees() else \
                ' with {0} minerals'.format(self.get_minerals()) if self.has_mineral_deposit() else \
                ' with unit {0}'.format(self.get_unit_ID())
        )

    def __repr__(self):
        return ('<' +
                super(Field, self).__repr__() +
                ' : ' +
                str(self)[1:-1] +
                '>')
