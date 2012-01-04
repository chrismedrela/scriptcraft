#!/usr/bin/env python
#-*- coding:utf-8 -*-

import os, shutil
import subprocess



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

    def execute_bash_command(self, command, input_data, dirty_folder_path):
        iterable_folder_path, folder = self._cleaned_path(dirty_folder_path)
        process = subprocess.Popen(command,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=folder)
        output, errors_output = process.communicate(input=input_data)
        exit_code = process.wait()
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