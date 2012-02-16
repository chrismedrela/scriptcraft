#!/usr/bin/env python
#-*- coding:utf-8 -*-

import hashlib
from collections import namedtuple

from scriptcraft.core.RunStatus import RunStatus
from scriptcraft.utils import *



STAR_PROGRAM = Const('star program')
def run_star_program(input):
    commands = []
    lines = iter(input.split('\n'))
    try:
        splited_first_line = lines.next().split()
        vision_diameter = int(splited_first_line[6])
        lines.next() # skip parameter
        for i in xrange(vision_diameter):
            lines.next() # skip description of surroundings
        for line in lines:
            line = line.strip()
            splited = line.split(None, 1)
            if len(splited) == 2:
                command = line[len(splited[0])+1:]
                commands.append(command)
    except (StopIteration, ValueError, IndexError):
        pass
    """
    for line in input.split('\n'):
        splited = line.strip().split(None, 1)
        if len(splited) == 2:
            maybe_number = splited[0]
            if len(maybe_number)<9:
                try:
                    int(maybe_number)
                except ValueError:
                    pass
                else:
                    command = line[len(maybe_number)+1:]
                    commands.append(command)
    """
    output = "\n".join(commands)

    return RunStatus(input=input,
                         output=output,
                         error_output='')


class Program(namedtuple("Program", ('language',
                                     'code'))):
    __slots__ = ()

    @ property
    def sha(self):
        sha = hashlib.sha1()
        sha.update(self.code)
        sha = sha.hexdigest()
        return sha

    def __str__(self):
        return "<Program %s in %s>" \
               % (self.sha, self.language.name)
