#!/usr/bin/env python
#-*- coding:utf-8 -*-

import hashlib
import os

from scriptcraft.core.Environment import Environment
from scriptcraft.utils import *



class CompileAndRunProgram(object):
    def __init__(self, directory,
                 source_file_names_by_languages,
                 binary_file_names_by_languages,
                 compilation_commands_by_languages,
                 running_commands_by_languages):
        self._directory = directory
        self._source_file_names_by_languages = source_file_names_by_languages
        self._binary_file_names_by_languages = binary_file_names_by_languages
        self._compilation_commands_by_languages = compilation_commands_by_languages
        self._running_commands_by_languages = running_commands_by_languages
        self._env = Environment(directory)

    def __call__(self, language, program_code, input_data):
        self._language = language
        self._program_code = program_code
        self._input_data = input_data
        hasher = hashlib.sha1()
        hasher.update(language)
        hasher.update(program_code)
        self._sha = hasher.hexdigest()
        self._compilation_command = self._compilation_commands_by_languages[language]
        self._running_command = self._running_commands_by_languages[language]
        self._source_file_name = self._source_file_names_by_languages[language]
        self._binary_file_name = self._binary_file_names_by_languages[language]

        compilation_status = self._compile()
        running_status = self._run()
        return (compilation_status, running_status)

    @ on_error_return((OSError, IOError), None)
    def _compile(self):
        if not self._is_compilation_necessary():
            return None
        self._clear_environment()
        self._create_source_file()
        compilation_status = self._execute_compilation_command()
        self._copy_binary_if_exists()
        return compilation_status

    def _is_compilation_necessary(self):
        binary = ('cache', self._sha)
        return not self._env.exists_file(binary)

    def _create_source_file(self):
        self._env.create_file(('env', self._source_file_name),
                              self._program_code)

    def _execute_compilation_command(self):
        input = ''
        directory = 'env'
        output, error_output, exit_status = \
            self._env.execute_bash_command(self._compilation_command,
                                           input, directory)
        return (output, error_output)

    def _copy_binary_if_exists(self):
        source = ('env', self._binary_file_name)
        destination = ('cache', self._sha)
        if self._env.exists_file(source):
            self._env.copy_file(source, destination)

    def _clear_environment(self):
        self._env.remove_folder_recursively('env')

    @ on_error_return((OSError, IOError), None)
    def _run(self):
        if not self._is_compilation_successful():
            return None
        self._clear_environment()
        self._copy_binary()
        self._create_source_file()
        running_status = self._execute_run_command()
        return running_status

    def _is_compilation_successful(self):
        return self._env.exists_file(('cache', self._sha))

    def _copy_binary(self):
        source = ('cache', self._sha)
        destination = ('env', self._binary_file_name)
        self._env.copy_file(source, destination)

    def _execute_run_command(self):
        input = self._input_data
        folder = 'env'
        output, error_output, exit_code = \
            self._env.execute_bash_command(self._running_command, input, folder)
        return (output, error_output)
