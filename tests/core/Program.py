#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.core.Program import run_star_program
from scriptcraft.core.RunStatus import RunStatus



class TestRunStarProgram(unittest.TestCase):
    def test_basic(self):
        input = """4 2 1 3 7 7 1
                   10
                   4 2 1
                   3 message
                   423\t message message
                   12"""
        excepted_output = ('message\n'
                           ' message message')
        excepted_error_output = ''

        run_status = run_star_program(input)
        excepted_run_status = RunStatus(input=input,
                                        output=excepted_output,
                                        error_output=excepted_error_output)
        self.assertEqual(run_status, excepted_run_status)
