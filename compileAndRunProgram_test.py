#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import os
import shutil

from utils import *
from compileAndRunProgram import CompileAndRunProgram
from Language import Language
from Program import Program
from CompilationStatus import CompilationStatus
from RunningStatus import RunningStatus

class TestCompileAndRunProgram(unittest.TestCase):
    def setUp(self):
        self.folder = "tmp_unittest"
        try:
            os.mkdir(self.folder)
        except OSError as ex:
            if ex.errno != 17: # folder already exists
                raise ex
        try:
            os.mkdir(os.path.join(self.folder, 'cache'))            
        except OSError as ex:
            if ex.errno != 17: # folder already exists
                raise ex        

    def test_cpp_program(self):
        program_text = """
            #include <stdio.h>
        
            using namespace std;
            
            int main() {
                printf("tekst outputowy\\nala");
                return 0;
            }
        """
        program_language = Language(
            ID=1,
            name="g++",
            source_extension=".cpp",
            binary_extension=".exe",
            compilation_command="gcc src.cpp -o bin.exe -lstdc++",
            running_command="./bin.exe",
        )
        program = Program(program_language, program_text)
        input = "input text\nbla bla"
        
        status = CompileAndRunProgram(program, input, self.folder)
        
        excepted_compilation_status = CompilationStatus(
            error_output = '',
            output = '',
        )
        excepted_running_status = RunningStatus(
            input = input,
            output = 'tekst outputowy\nala',
            error_output = '',
        )
        self.assertEqual(status.maybe_compilation_status, excepted_compilation_status)
        self.assertEqual(status.maybe_running_status, excepted_running_status)

    def tearDown(self):
        shutil.rmtree(self.folder)

if __name__ == '__main__':
    unittest.main()
