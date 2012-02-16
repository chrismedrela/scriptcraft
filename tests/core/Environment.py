#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import os

from scriptcraft.core.Environment import Environment

from scriptcraft.utils import *



class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.main_folder = 'tmp_unittest_test_environment'
        self.simple_data = 'data data data'
        self.file_system = TemporaryFileSystem(self.main_folder)
        self.env = Environment(self.main_folder)

    def tearDown(self):
        self.file_system.delete_files_and_folders()

    def test_create_file(self):
        path = 'my_file.txt'
        self._test_create_file_with_simple_data(path=path,
                                                path_as_iterable=path)

    def test_create_file_when_path_is_iterable(self):
        self.file_system.create_folder_if_necessary('folder')
        self.file_system.create_folder_if_necessary('folder/subfolder')
        path_as_iterable = ('folder', 'subfolder', 'file.file_extension')
        path = os.path.join(*path_as_iterable)

        self._test_create_file_with_simple_data(path, path_as_iterable)

    def _test_create_file_with_simple_data(self, path, path_as_iterable):
        self.env.create_file(path_as_iterable, self.simple_data)

        self.assertTrue(self.file_system.exists_file_or_folder(path))
        self.assertEqual(self.file_system.read_file(path),
                         self.simple_data)

    def test_creating_file_raise_error_when_the_file_exists(self):
        self.file_system.write_file('file', self.simple_data)
        operation = lambda: self.env.create_file('file', self.simple_data)
        self.assertRaises(IOError, operation)

    def test_file_exists(self):
        folder_name = 'folder'
        self.file_system.create_folder_if_necessary(folder_name)
        path_as_iterable = (folder_name, 'file.txt')
        path = os.path.join(*path_as_iterable)
        self.file_system.write_file(path, data='')

        file_exists = self.env.exists_file(path_as_iterable)

        self.assertTrue(file_exists)

    def test_file_exists_returns_False_when_folder_with_the_same_name_exists(self):
        path = 'folder'
        self.file_system.create_folder_if_necessary(path)

        exists_file = self.env.exists_file(path)

        self.assertFalse(exists_file)

    def test_remove_folder_recursively(self):
        file_not_to_remove = 'file_not_to_remove.dat'
        self.file_system.write_file(file_not_to_remove, self.simple_data)

        self.file_system.create_folder_if_necessary('to_remove')
        self.file_system.write_file('to_remove/file1.txt', self.simple_data)
        self.file_system.create_folder_if_necessary('to_remove/subfolder')
        self.file_system.write_file('to_remove/subfolder/file2.txt', self.simple_data)

        self.env.remove_folder_recursively('to_remove')

        self.assertTrue(self.file_system.exists_file_or_folder(file_not_to_remove))
        self.assertFalse(self.file_system.exists_file_or_folder('to_remove'))

    def test_remove_nonexistent_folder(self):
        folder = 'folder'
        assert not self.file_system.exists_file_or_folder(folder)

        # it should *not* raise an exception
        self.env.remove_folder_recursively(folder)

    def test_copy_file(self):
        self.file_system.create_folder_if_necessary('folder')
        source_path_as_iterable = ('folder', 'file.src')
        source_path = os.path.join(*source_path_as_iterable)
        self.file_system.write_file(source_path, self.simple_data)

        self.file_system.create_folder_if_necessary('destfolder')
        destination_path_as_iterable = ('destfolder', 'file.dest')
        destination_path = os.path.join(*destination_path_as_iterable)

        self.env.copy_file(source_path_as_iterable, destination_path_as_iterable)

        self.assertTrue(self.file_system.exists_file_or_folder(source_path))
        self.assertEqual(self.file_system.read_file(destination_path),
                         self.simple_data)

    def test_copy_file_raise_exception_if_destination_file_exists(self):
        source_path = 'file.src'
        destination_path = 'file.dest'
        self.file_system.write_file(source_path, self.simple_data)
        self.file_system.write_file(destination_path, self.simple_data)

        illegal_operation = lambda: self.env.copy_file(source_path,
                                                       destination_path)
        self.assertRaises(IOError, illegal_operation)

    def test_creating_folder_raise_error_when_file_with_the_same_name_exists(self):
        name = 'collision'
        self.file_system.write_file(name, self.simple_data)
        operation = lambda: self.env.create_file((name, 'file.txt'),
                                                 self.simple_data)
        self.assertRaises(IOError, operation)

    def test_execute_bash_command(self):
        input_data = ''
        command = 'echo bla bla && unknown_command'
        folder = ''

        output, error_output, exit_code = \
            self.env.execute_bash_command(command, input_data, folder)

        self.assertEqual(output, 'bla bla\n')
        self.assertTrue(error_output != '')
        self.assertTrue(exit_code != 0)
