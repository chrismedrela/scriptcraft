#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple



class Message(namedtuple('Message', ('sender_ID',
                                     'receiver_ID',
                                     'text'))):
    """
    Attributes 'sender_ID' and 'receiver_ID' might be equal to zero. It means that
    the sender/receiver is game system.

    """

    __slots__ = ()
