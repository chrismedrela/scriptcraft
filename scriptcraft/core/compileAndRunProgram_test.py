#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.utils import *
from scriptcraft.core.CompilationStatus import CompilationStatus
from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.Language import Language
from scriptcraft.core.Program import Program
from scriptcraft.core.RunStatus import RunStatus


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.folder = "tmp_unittest"
        self.file_system = TemporaryFileSystem(self.folder)
        self.file_system.create_folder_if_necessary('cache')

    def tearDown(self):
        self.file_system.delete_files_and_folders()

    def test_cpp_program(self):
        program_code = self._build_valid_cpp_code()
        program = self._build_cpp_program(program_code)
        input = "input text\nbla bla"

        status = CompileAndRunProgram(program, input, self.folder)

        expected_compilation_status = self._build_successful_compilation_status()
        expected_running_status = self._build_successful_running_status()
        self.assertEqual(status.maybe_compilation_status, expected_compilation_status)
        self.assertEqual(status.maybe_running_status, expected_running_status)

    def test_environment_folder_already_exists(self):
        self.file_system.create_folder_if_necessary('env')
        self.test_cpp_program()

    def test_invalid_program(self):
        program_code = ""
        program = self._build_cpp_program(program_code)
        input = ""

        status = CompileAndRunProgram(program, input, self.folder)

        expected_compilation_status = CompilationStatus(
            error_output = ("/usr/lib/gcc/x86_64-linux-gnu/4.4.3/../../../../lib/crt1.o: In function `_start':\n"
                            "(.text+0x20): undefined reference to `main'\n"
                            "collect2: ld returned 1 exit status\n"),
            output = '',
        )
        expected_running_status = None
        self.assertEqual(status.maybe_compilation_status, expected_compilation_status)
        self.assertEqual(status.maybe_running_status, expected_running_status)

    def test_compilation_not_necessary(self):
        program_code = self._build_valid_cpp_code()
        program = self._build_cpp_program(program_code)
        input = "input text\nbla bla"

        status = CompileAndRunProgram(program, input, self.folder)  # compile and run
        status = CompileAndRunProgram(program, input, self.folder)  # now compilation is not necessary

        expected_running_status = self._build_successful_running_status()
        self.assertTrue(status.maybe_compilation_status is None)
        self.assertEqual(status.maybe_running_status, expected_running_status)

    def _build_cpp_program(self, code):
        return Program(self._build_cpp_language(), code)

    def _build_cpp_language(self):
        program_language = Language(ID=1,
                                    name="g++",
                                    source_extension=".cpp",
                                    binary_extension=".exe",
                                    compilation_command="gcc src.cpp -o bin.exe -lstdc++",
                                    running_command="./bin.exe")
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
        return RunStatus(input="input text\nbla bla",
                             output='tekst outputowy\nala',
                             error_output='')
