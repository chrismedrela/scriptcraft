#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os
import shutil
import subprocess

from scriptcraft.core.Program import Program
from scriptcraft.core.RunningStatus import RunningStatus
from scriptcraft.core.CompilationStatus import CompilationStatus

class CompileAndRunProgram(object):
    def __init__(self, program, input, folder):
        self.program = program
        self.input = input
        self.folder = folder

        self.maybe_compilation_status = self._compile()
        self.maybe_running_status = self._run()

    def _compile(self):
        try:
            return self._try_compile()
        except (OSError, IOError):
            return None

    def _try_compile(self):
        if not self._is_compilation_necessary():
            return None
        self._create_environment_folder_if_necessary()
        self._create_source_file()
        compilation_status = self._execute_compilation_command()
        self._copy_binary_if_exists()
        self._clear_environment()
        return compilation_status

    def _is_compilation_necessary(self):
        sha = self.program.sha()
        binary_file_path = os.path.join(self.folder, 'cache', sha)
        compilation_necessary = not os.path.exists(binary_file_path)
        return compilation_necessary

    def _create_environment_folder_if_necessary(self):
        env_folder = os.path.join(self.folder, 'env')
        try:
            os.mkdir(env_folder)
        except OSError as ex:
            FOLDER_ALREADY_EXISTS = 17
            if ex.errno != FOLDER_ALREADY_EXISTS:
                raise

    def _create_source_file(self):
        source_file_path = os.path.join(self.folder, 'env', self.program.language.source_file_name)
        with open(source_file_path, 'w') as stream:
            stream.write(self.program.code)

    def _execute_compilation_command(self):
        input = ''
        folder = os.path.join(self.folder, 'env')
        output, error_output = self._execute_bash_command(self.program.language.compilation_command, input, folder)
        return CompilationStatus(output, error_output)

    def _copy_binary_if_exists(self):
        source = os.path.join(self.folder, 'env', self.program.language.binary_file_name)
        if os.path.exists(source):
            sha = self.program.sha()
            self._create_cache_folder_if_necessary()
            destination = os.path.join(self.folder, 'cache', sha)
            shutil.copy(source, destination)

    def _create_cache_folder_if_necessary(self):
        cache_folder = os.path.join(self.folder, 'cache')
        try:
            os.mkdir(cache_folder)
        except OSError as ex:
            FOLDER_ALREADY_EXISTS = 17
            if ex.errno != FOLDER_ALREADY_EXISTS:
                raise

    def _clear_environment(self):
        env_folder = os.path.join(self.folder, 'env')
        shutil.rmtree(env_folder)

    def _run(self):
        try:
            return self._try_run()
        except (OSError, IOError):
            return None

    def _try_run(self):
        if not self._is_compilation_successful():
            return None
        self._create_environment_folder_if_necessary()
        self._copy_binary()
        self._create_source_file()
        running_status = self._execute_run_command()
        self._clear_environment()
        return running_status

    def _is_compilation_successful(self):
        binary_file_name = self.program.sha()
        binary_file_path = os.path.join(self.folder, 'cache', binary_file_name)
        return os.path.exists(binary_file_path)

    def _copy_binary(self):
        sha = self.program.sha()
        source = os.path.join(self.folder, 'cache', sha)
        destination = os.path.join(self.folder, 'env', self.program.language.binary_file_name)
        shutil.copy(source, destination)

    def _execute_run_command(self):
        input = self.input
        folder = os.path.join(self.folder, 'env')
        output, error_output = self._execute_bash_command(self.program.language.running_command, input, folder)
        return RunningStatus(input, output, error_output)

    def _execute_bash_command(self, command, input_data, folder):
    	process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=folder)
        output, errors_output = process.communicate(input=input_data)
    	exit_code = process.wait()
    	return output, errors_output

