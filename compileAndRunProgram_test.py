#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import os

from utils import *

from compileAndRunProgram import CompileAndRunProgram


class TestCompileAndRunProgram(unittest.TestCase):
    def test_cpp_program(self):
        program_text = """
            using namespace std;
            
            int main() {
                printf('tekst outputowy\nala');
                return 0;
            }
        """
        program_language = Language(
            ID=1,
            name="cpp",
            source_extension=".cpp",
            binary_extension=".exe",
            compilation_command="gcc source.cpp -o binary.exe",
            running_command="./binary.exe",
        )
        folder = "tmp_unittest"
        try:
            os.mkdir(folder)
        except OSError as ex:
            if not ex.errno == 19:
                raise ex
        program = Program(program_language, program_text)
        input = "input text\nbla bla"
        
        status = CompileAndRunProgram(program, input, folder)
        
        excepted_compilation_status = CompilationStatus(
            error_output = '',
            output = '',
        )
        excepted_running_status = RunningStatus(
            input = input,
            output = 'tekst outputowy\nala',
            err_output = '',
        )
        self.assertEqual(status.compilation_done, True)
        self.assertEqual(status.compilation_status, excepted_compilation_status)
        self.assertEqual(status.running_done, True)
        self.assertEqual(status.running_status, excepted_running_status)


if __name__ == '__main__':
    unittest.main()
