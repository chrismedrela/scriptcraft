#!/usr/bin/env python
#-*- coding:utf-8 -*-

import hashlib
import os
import shutil
import stat
import subprocess

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


class Environment(object):
    """
    All methods may raise OSError or IOError.
    """

    def __init__(self, main_folder):
        self.main_folder = main_folder

    def exists_file(self, dirty_path):
        iterable_path, path = self._cleaned_path(dirty_path)
        return os.path.exists(path) and os.path.isfile(path)

    def create_file(self, path, data):
        iterable_path, path = self._cleaned_path(path)
        self._create_folder_if_necessary_for_file(iterable_path)
        if os.path.exists(path):
            raise IOError('Cannot create folder - the file with the same name exists.')
        with open(path, 'w') as s:
            s.write(data)

    def remove_folder_recursively(self, dirty_path):
        iterable_path, path = self._cleaned_path(dirty_path)
        if os.path.exists(path):
            shutil.rmtree(path)

    def copy_file(self, source_path, destination_path):
        iterable_source_path, source_path = self._cleaned_path(source_path)
        iterable_destination_path, destination_path = self._cleaned_path(destination_path)
        self._create_folder_if_necessary_for_file(iterable_destination_path)
        if os.path.exists(destination_path):
            raise IOError("File with destination name exists")
        shutil.copyfile(source_path, destination_path)
        try:
            os.chmod(destination_path, stat.S_IRWXU)
        except OSError:
            pass

    def execute_bash_command(self, command, input_data, dirty_folder_path):
        iterable_folder_path, folder = self._cleaned_path(dirty_folder_path)
        process = subprocess.Popen(command,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=folder)

        # pass input data to the process
        try:
            process.stdin.write(input_data)
        except IOError as ex:
            if ex.errno != 32: # not broken pipe error
                raise
        finally:
            process.stdin.close()

        # read output and finish
        exit_code = process.wait()
        output = process.stdout.read()
        errors_output = process.stderr.read()
        return output, errors_output, exit_code

    def _cleaned_path(self, dirty_path):
        if isinstance(dirty_path, basestring):
            dirty_path = (dirty_path,)
        path_as_iterable = (self.main_folder,) + tuple(dirty_path)
        path = os.path.join(*path_as_iterable)
        return path_as_iterable, path

    def _create_folder_if_necessary_for_file(self, path_with_filename):
        path_without_filename = path_with_filename[:-1]
        full_path = []
        for folder in path_without_filename:
            full_path.append(folder)
            path = os.path.join(*full_path)
            self._create_folder_if_necessary_for_path(path)

    def _create_folder_if_necessary_for_path(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            if not os.path.isdir(path):
                raise IOError('Cannot create folder - the file with the same name exists.')

