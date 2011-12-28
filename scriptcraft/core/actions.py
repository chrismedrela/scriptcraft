#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Following actions are avaiable:
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

class MoveAction(namedtuple('MoveAction', ('source', 'destination'))):
    __slots__ = ()

class GatherAction(namedtuple('GatherAction', ('source',))):
    __slots__ = ()

class StoreAction(namedtuple('StoreAction', ('storage_ID',))):
    __slots__ = ()

class FireAction(namedtuple('FireAction', ('destination',))):
    __slots__ = ()

class BuildAction(namedtuple('BuildAction', ('unit_type', 'destination'))):
    __slots__ = ()
