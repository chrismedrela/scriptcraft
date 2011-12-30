#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import os
import shutil

from scriptcraft.utils import *
from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.Language import Language
from scriptcraft.core.Program import Program
from scriptcraft.core.CompilationStatus import CompilationStatus
from scriptcraft.core.RunningStatus import RunningStatus

class TestBasic(unittest.TestCase):

    def setUp(self):
        self.folder = "tmp_unittest"

        os.mkdir(self.folder)
        os.mkdir(os.path.join(self.folder, 'cache'))


    def tearDown(self):
        shutil.rmtree(self.folder)


    def test_cpp_program(self):
        program_code = self._build_valid_cpp_code()
        program = self._build_cpp_program(program_code)
        input = "input text\nbla bla"

        status = CompileAndRunProgram(program, input, self.folder)

        excepted_compilation_status = self._build_successful_compilation_status()
        excepted_running_status = self._build_successful_running_status()

        self.assertEqual(status.maybe_compilation_status, excepted_compilation_status)
        self.assertEqual(status.maybe_running_status, excepted_running_status)


    def test_environment_folder_already_exists(self):
        os.mkdir(os.path.join(self.folder, 'env'))

        self.test_cpp_program()


    def test_invalid_program(self):
        program_code = ""
        program = self._build_cpp_program(program_code)
        input = ""

        status = CompileAndRunProgram(program, input, self.folder)

        excepted_compilation_status = CompilationStatus(
            error_output = "/usr/lib/gcc/x86_64-linux-gnu/4.4.3/../../../../lib/crt1.o: In function `_start':\n(.text+0x20): undefined reference to `main'\ncollect2: ld returned 1 exit status\n",
            output = '',
        )
        excepted_running_status = None

        self.assertEqual(status.maybe_compilation_status, excepted_compilation_status)
        self.assertEqual(status.maybe_running_status, excepted_running_status)


    def test_os_problems(self):
        program_code = self._build_valid_cpp_code()
        program = self._build_cpp_program(program_code)
        input = ""

        def raise_IO_Error(self):
            raise IOError()
        old_try_run = CompileAndRunProgram._try_run
        CompileAndRunProgram._try_run = raise_IO_Error

        status = CompileAndRunProgram(program, input, self.folder)

        excepted_running_status = None
        self.assertEqual(status.maybe_running_status, excepted_running_status)

        CompileAndRunProgram._try_run = old_try_run



    def test_compilation_not_necessary(self):
        program_code = self._build_valid_cpp_code()
        program = self._build_cpp_program(program_code)
        input = "input text\nbla bla"

        status = CompileAndRunProgram(program, input, self.folder)
        status = CompileAndRunProgram(program, input, self.folder)

        excepted_compilation_status = self._build_successful_compilation_status()
        excepted_running_status = self._build_successful_running_status()

        self.assertEqual(status.maybe_compilation_status, None)
        self.assertEqual(status.maybe_running_status, excepted_running_status)

    def _build_cpp_program(self, code):
        return Program(self._build_cpp_language(), code)

    def _build_cpp_language(self):
        program_language = Language(ID=1,
            name="g++",
            source_extension=".cpp",
            binary_extension=".exe",
            compilation_command="gcc src.cpp -o bin.exe -lstdc++",
            running_command="./bin.exe"
        )
        return program_language

    def _build_valid_cpp_code(self):
        return """
            #include <stdio.h>

            using namespace std;

            int main() {
                printf("tekst outputowy\\nala");
                return 0;
            }
        """

    def _build_successful_compilation_status(self):
        return CompilationStatus(error_output='', output='')

    def _build_successful_running_status(self):
        return RunningStatus(input="input text\nbla bla", output='tekst outputowy\nala', error_output='')

