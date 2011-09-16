#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from utils import *

from compileAndRunProgram import CompileAndRunProgram


"""
class TestParse(unittest.TestCase):

	def test_basic(self):
		p = Parse("", 2)
		self.assertEqual(p.messages, [])
		self.assertEqual(p.commands, [])
		self.assertEqual(p.invalid_lines_numbers, [])
		
class TestEfficiencyParsingCommands(unittest.TestCase):
	def setUp(self):
		self.input_data = ('S\n')*5000

	@ max_time(150, repeat=3)
	def test(self):
		p = Parse(self.input_data, 2)
"""

if __name__ == '__main__':
	unittest.main()
