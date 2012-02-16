#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Following actions are available:

StopAction
MoveAction
GatherAction
StoreAction
FireAction
BuildAction

"""


from collections import namedtuple


class StopAction(namedtuple('StopAction', ())):
    __slots__ = ()

    def __str__(self):
        return '<Action stop>'


class MoveAction(namedtuple('MoveAction',
                            ('source', 'destination'))):
    __slots__ = ()

    def __str__(self):
        return '<Action move from (%d, %d) to (%d, %d)>' \
               % (self.source[0], self.source[1],
                  self.destination[0], self.destination[1])


class GatherAction(namedtuple('GatherAction',
                              ('source',))):
    __slots__ = ()

    def __str__(self):
        return '<Action gather from (%d, %d)>' \
               % (self.source[0], self.source[1])


class StoreAction(namedtuple('StoreAction',
                             ('storage_ID',))):
    __slots__ = ()

    def __str__(self):
        return '<Action store to unit %d>' % self.storage_ID


class FireAction(namedtuple('FireAction',
                            ('destination',))):
    __slots__ = ()

    def __str__(self):
        return '<Action fire at (%d, %d)>' \
               % (self.destination[0], self.destination[1])


class BuildAction(namedtuple('BuildAction',
                             ('unit_type', 'destination'))):
    __slots__ = ()

    def __str__(self):
        return '<Action build %s at (%d, %d)>' \
               % (self.unit_type.main_name,
                  self.destination[0], self.destination[1])

