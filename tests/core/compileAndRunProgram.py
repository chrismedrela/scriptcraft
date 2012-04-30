#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.utils import *
from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.Language import Language
from scriptcraft.core.Program import Program


class TestBasic(unittest.TestCase):

    def setUp(self):
        self.directory = "tmp_unittest"
        self.file_system = TemporaryFileSystem(self.directory)
        self.file_system.create_folder_if_necessary('cache')

    def tearDown(self):
        self.file_system.delete_files_and_folders()

    def test_cpp_program(self):
        program_code = self._build_valid_cpp_code()
        input_data = "input text\nbla bla"

        compile_and_run = self._build_compile_and_run_program_instance()
        status = compile_and_run(Language.CPP, program_code, input_data)

        maybe_compilation_status, maybe_running_status = status
        expected_compilation_status = ('', '')
        expected_running_status = ('tekst outputowy\nala', '')
        self.assertEqual(maybe_compilation_status, expected_compilation_status)
        self.assertEqual(maybe_running_status, expected_running_status)

    def test_environment_folder_already_exists(self):
        self.file_system.create_folder_if_necessary('env')
        self.test_cpp_program()

    def test_invalid_program(self):
        program_code = ""
        input_data = ""

        compile_and_run = self._build_compile_and_run_program_instance()
        status = compile_and_run(Language.CPP, program_code, input_data)

        maybe_compilation_status, maybe_running_status = status
        expected_compilation_status = (
            '',
            ("/usr/lib/gcc/x86_64-linux-gnu/4.4.3/"
             "../../../../lib/crt1.o: In function `_start':\n"
             "(.text+0x20): undefined reference to `main'\n"
             "collect2: ld returned 1 exit status\n"),
        )
        expected_running_status = None
        self.assertEqual(maybe_compilation_status, expected_compilation_status)
        self.assertEqual(maybe_running_status, expected_running_status)

    def test_compilation_not_necessary(self):
        program_code = self._build_valid_cpp_code()
        input_data = "input text\nbla bla"

        compile_and_run = self._build_compile_and_run_program_instance()
        # compile and run
        status = compile_and_run(Language.CPP, program_code, input_data)
        # now compilation is not necessary
        status = compile_and_run(Language.CPP, program_code, input_data)

        maybe_compilation_status, maybe_running_status = status
        expected_running_status = ('tekst outputowy\nala', '')
        self.assertTrue(maybe_compilation_status is None)
        self.assertEqual(maybe_running_status, expected_running_status)

    def _build_compile_and_run_program_instance(self):
        result = CompileAndRunProgram(self.directory,
                                      {Language.CPP:'src.cpp'},
                                      {Language.CPP:'bin.exe'},
                                      {Language.CPP:'g++ src.cpp -o bin.exe'},
                                      {Language.CPP:'./bin.exe'})
        return result

    def _build_valid_cpp_code(self):
        return """
            #include <stdio.h>

            using namespace std;

            int main() {
                printf("tekst outputowy\\nala");
                return 0;
            }
        """


