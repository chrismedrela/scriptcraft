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

    def exists_file(self, path):
        path = self._get_path(path)
        return os.path.exists(path) and os.path.isfile(path)

    def create_file(self, path, data):
        path_as_iterable = self._get_path_as_iterable(path)
        path_without_filename = path_as_iterable[:-1]
        self._create_folder_if_necessary(path_without_filename)
        path = os.path.join(*path_as_iterable)
        with open(path, 'w') as s:
            s.write(data)

    def remove_folder_recursively(self, folder_path):
        path = self._get_path(folder_path)
        if os.path.exists(path):
            shutil.rmtree(path)

    def copy_file(self, source_path, destination_path):
        source_path = self._get_path(source_path)
        destination_path_as_iterable = self._get_path_as_iterable(destination_path)
        destination_path_without_filename = destination_path_as_iterable[:-1]
        self._create_folder_if_necessary(destination_path_without_filename)
        destination_path = os.path.join(*destination_path_as_iterable)
        if os.path.exists(destination_path):
            raise IOError("File with destination name exists")
        shutil.copyfile(source_path, destination_path)

    def execute_bash_command(self, command, input_data, folder):
        folder = self._get_path(folder)
        process = subprocess.Popen(command,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   shell=True,
                                   cwd=folder)
        output, errors_output = process.communicate(input=input_data)
        exit_code = process.wait()
        return output, errors_output, exit_code

    def _get_path(self, path):
        path = self._get_path_as_iterable(path)
        return os.path.join(*path)

    def _get_path_as_iterable(self, path):
        if isinstance(path, basestring):
            path = (path,)
        path = (self.main_folder,) + tuple(path)
        return path

    def _create_folder_if_necessary(self, folder_path):
        full_path = []
        for folder in folder_path:
            full_path.append(folder)
            path = os.path.join(*full_path)
            self._create_folder_if_necessary_for_path(path)

    def _create_folder_if_necessary_for_path(self, path):
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            if not os.path.isdir(path):
                raise IOError('Cannot create folder - the file with the same name exists.')
