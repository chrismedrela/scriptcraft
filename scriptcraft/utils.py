#!/usr/bin/env python
#-*- coding:utf-8 -*-

__all__ = [
    'Enum',
    'make_enum',
    'max_time',
    'anything',
    'skip',
    'distance',
    'copy_if_an_instance_given',
]

import time
from enum import Enum, make_enum
from functools import wraps



def copy_if_an_instance_given(f):
    """ Decorator. Use with method __new__ of classes inheriting namedtuple.
    Allow to make a copy instance by passing it as an only argument.

    What's more, if you implement __deepcopy__ like this:

      def __deepcopy__(self, memo):
          c = MyClass(self)
          return c

    you can use deepcopy on your classes inheriting namedtuple with your own
    implementation of __new__ method.

    """

    @ wraps(f)
    def wraper(cls, *args, **kwargs):
        if len(args) == 1 and type(args[0]) == cls and len(kwargs) == 0:
            self = args[0]
            l = [getattr(self, field) for field in cls._fields]
            return cls.__bases__[0].__new__(cls, *l)

        return f(cls, *args, **kwargs)

    return wraper


def distance(p1, p2):
    """ Return distance between p1=(x1,y1) and p2=(x2,y2). Use town metric. """
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])


def skip(f):
    def wrapped(*args, **kwargs):
        pass
    return wrapped


class _Anything(object):
    def __eq__(self, other):
        return True
anything = _Anything()



class max_time(object):
    """ Dekorator do testów wydajnościowych - oznaczony tym dekoratorem test
    zawodzi, jeżeli zostanie przekroczony dany czas podany w milisekundach. """

    def __init__(self, max_time_in_miliseconds, repeat=1):
        self.max_time = max_time_in_miliseconds
        self.repeat = repeat


    def __call__(self, f):

        def result(test_case, *args, **kwargs):
            times = []
            for _ in xrange(self.repeat):
                start_time = time.time()
                f(test_case, *args, **kwargs)
                end_time = time.time()

                delta_time_in_miliseconds = (end_time-start_time)*1000
                times.append(delta_time_in_miliseconds)

            average = sum(times)/self.repeat
            if average > self.max_time:
                formated_times = ", ".join(map(lambda t: "%.2f ms" % t, times))
                test_case.fail('Too long average executing time  %.2f ms (max  %.2f ms); times: %s.' % \
                    (average, self.max_time, formated_times))

        return result



