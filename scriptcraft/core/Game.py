#!/usr/bin/env python
#-*- coding:utf-8 -*-

class Game(object):
    pass

class InvalidReceiver(Exception):
    pass

class PositionOutOfMap(Exception):
    pass

class CannotStoreMinerals(Exception):
    pass

class FieldIsOccupied(Exception):
    pass