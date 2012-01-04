#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import shutil
import subprocess

from scriptcraft.core.CompilationStatus import CompilationStatus
from scriptcraft.core.Environment import Environment
from scriptcraft.core.Program import Program
from scriptcraft.core.RunningStatus import RunningStatus



class CompileAndRunProgram(object):
    def __init__(self, program, input, folder):
        self.program = program
        self.input = input
        self.folder = folder
        self.env = Environment(folder)

        self.maybe_compilation_status = self._compile()
        self.maybe_running_status = self._run()

    def _compile(self):
        try:
            return self._try_compile()
        except (OSError, IOError):
            import traceback
            print 'a'
            traceback.print_exc()
            return None

    def _try_compile(self):
        if not self._is_compilation_necessary():
            return None
        self._create_source_file()
        compilation_status = self._execute_compilation_command()
        self._copy_binary_if_exists()
        self._clear_environment()
        return compilation_status

    def _is_compilation_necessary(self):
        binary = ('cache', self.program.sha())
        return not self.env.exists_file(binary)

    def _create_source_file(self):
        self.env.create_file(('env', self.program.language.source_file_name),
                             self.program.code)

    def _execute_compilation_command(self):
        input = ''
        folder = 'env'
        output, error_output, exit_status = \
            self.env.execute_bash_command(self.program.language.compilation_command,
                                          input, folder)
        return CompilationStatus(output, error_output)

    def _copy_binary_if_exists(self):
        source = ('env', self.program.language.binary_file_name)
        destination = ('cache', self.program.sha())
        if self.env.exists_file(source):
            self.env.copy_file(source, destination)

    def _create_cache_folder_if_necessary(self):
        cache_folder = os.path.join(self.folder, 'cache')
        self._create_folder_if_necessary(cache_folder)

    def _clear_environment(self):
        self.env.remove_folder_recursively('env')

    def _run(self):
        try:
            return self._try_run()
        except (OSError, IOError):
            import traceback
            print 'a'
            traceback.print_exc()
            return None

    def _try_run(self):
        if not self._is_compilation_successful():
            return None
        self._copy_binary()
        self._create_source_file()
        running_status = self._execute_run_command()
        self._clear_environment()
        return running_status

    def _is_compilation_successful(self):
        return self.env.exists_file(('cache', self.program.sha()))

    def _copy_binary(self):
        source = ('cache', self.program.sha())
        destination = ('env', self.program.language.binary_file_name)
        self.env.copy_file(source, destination)

    def _execute_run_command(self):
        input = self.input
        folder = 'env'
        output, error_output, exit_code = \
            self.env.execute_bash_command(self.program.language.running_command,
                                          input, folder)
        return RunningStatus(input, output, error_output)
