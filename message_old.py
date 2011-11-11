#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
sender_ID i receiver_ID mogą być równe zero; wtedy oznacza to, że nadawcą/odbiorcą
jest system gry.

"""

from collections import namedtuple

Message = namedtuple('Message', ['sender_ID', 'receiver_ID', 'text'])

