#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from utils import *

from compileAndRunProgram import CompileAndRunProgram


class TestCompileAndRunProgram(unittest.TestCase):
	def test_cpp_program(self):
		program_text = """
			using namespace std;
			
			int main() {
				return 0;
			}
		"""
		program_language = Language(
			#TODO
		)
		program = Program(program_language, program_text)
		input = ""
		
		status = CompileAndRunProgram(program, input)
		
		excepted_compilation_status = CompilationStatus(
			error_output = '',
			output = '',
		)
		excepted_running_status = RunningStatus(
			input = input,
			output = '',
			err_output = '',
		)
		self.assertEqual(status.compilation_done, True)
		self.assertEqual(status.compilation_status, excepted_compilation_status)
		self.assertEqual(status.running_done, True)
		self.assertEqual(status.running_status, excepted_running_status)


"""	
class TestEfficiencyParsingCommands(unittest.TestCase):
	def setUp(self):
		self.input_data = ('S\n')*5000

	@ max_time(150, repeat=3)
	def test(self):
		p = Parse(self.input_data, 2)
"""

if __name__ == '__main__':
	unittest.main()
