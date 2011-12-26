#!/usr/bin/env python
#-*- coding:utf-8 -*-

__all__ = [
    'Enum',
    'make_enum',
    'max_time',
    'distance',
]

import time
from enum import Enum, make_enum

def distance(p1, p2):
    """ Return distance between p1=(x1,y1) and p2=(x2,y2). Use town metric. """
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

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



