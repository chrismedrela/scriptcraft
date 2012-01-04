#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import shutil, os

from scriptcraft.core.Environment import Environment
from os import environ



class TestEnvironment(unittest.TestCase):
    def setUp(self):
        self.main_folder = 'tmp_unittest_test_environment'
        self.simple_data = 'data data data'
        self._temporary_files = []
        self._temporary_folders = []
        self._create_temporary_folder_if_necessary('')
        self.env = Environment(self.main_folder)

    def tearDown(self):
        self._delete_temporary_files_and_folders()

    def test_create_file(self):
        path = 'my_file.txt'
        self._test_create_file_with_simple_data(path=path,
                                                path_as_iterable=path)

    def test_create_file_when_path_is_iterable(self):
        self._create_temporary_folder_if_necessary('folder')
        self._create_temporary_folder_if_necessary('folder/subfolder')
        path_as_iterable = ('folder', 'subfolder', 'file.file_extension')
        path = os.path.join(*path_as_iterable)

        self._test_create_file_with_simple_data(path, path_as_iterable)

    def _test_create_file_with_simple_data(self, path, path_as_iterable):
        self.env.create_file(path_as_iterable, self.simple_data)

        self.assertTrue(self._exists_temporary_file_or_folder(path))
        self.assertEqual(self._read_temporary_file(path),
                         self.simple_data)

    def test_file_exists(self):
        folder_name = 'folder'
        self._create_temporary_folder_if_necessary(folder_name)
        path_as_iterable = (folder_name, 'file.txt')
        path = os.path.join(*path_as_iterable)
        self._write_temporary_file(path, data='')

        file_exists = self.env.exists_file(path_as_iterable)

        self.assertTrue(file_exists)

    def test_file_exists_returns_False_when_folder_with_the_same_name_exists(self):
        path = 'folder'
        self._create_temporary_folder_if_necessary(path)

        exists_file = self.env.exists_file(path)

        self.assertFalse(exists_file)

    def test_remove_folder_recursively(self):
        self._create_temporary_folder_if_necessary('to_remove')
        self._create_temporary_folder_if_necessary('to_remove/subfolder')
        file_not_to_remove = 'file_not_to_remove.dat'
        self._write_temporary_file(file_not_to_remove, self.simple_data)
        self._write_temporary_file('to_remove/file1.txt', self.simple_data)
        self._write_temporary_file('to_remove/subfolder/file2.txt', self.simple_data)
        folder_path = 'to_remove'

        self.env.remove_folder_recursively(folder_path)

        self.assertTrue(self._exists_temporary_file_or_folder(file_not_to_remove))
        self.assertFalse(self._exists_temporary_file_or_folder(folder_path))

    def test_remove_nonexistent_folder(self):
        folder = 'folder'
        assert not os.path.exists(folder)

        # it should *not* raise an exception
        self.env.remove_folder_recursively(folder)

    def test_copy_file(self):
        source_path_as_iterable = ('folder', 'file.src')
        source_path = os.path.join(*source_path_as_iterable)
        destination_path_as_iterable = ('destfolder', 'file.dest')
        destination_path = os.path.join(*destination_path_as_iterable)
        self._create_temporary_folder_if_necessary('folder')
        self._create_temporary_folder_if_necessary('destfolder')
        self._write_temporary_file(source_path, self.simple_data)

        self.env.copy_file(source_path_as_iterable, destination_path_as_iterable)

        self.assertTrue(self._exists_temporary_file_or_folder(source_path))
        self.assertEqual(self._read_temporary_file(destination_path),
                         self.simple_data)

    def test_copy_file_raise_exception_if_destination_file_exists(self):
        source_path = 'file.src'
        destination_path = 'file.dest'
        self._write_temporary_file(source_path, self.simple_data)
        self._write_temporary_file(destination_path, self.simple_data)

        illegal_operation = lambda: self.env.copy_file(source_path,
                                                       destination_path)
        self.assertRaises(IOError, illegal_operation)

    def test_execute_bash_command(self):
        input_data = ''
        command = 'echo bla bla && unknown_command'

        output, error_output, exit_code = \
            self.env.execute_bash_command(command, input_data)

        self.assertEqual(output, 'bla bla\n')
        self.assertTrue(error_output != '')
        self.assertTrue(exit_code != 0)

# temporary files and folders system -------------------------------------------
    def _write_temporary_file(self, file_path, data):
        file_path = os.path.join(self.main_folder, file_path)
        assert not os.path.exists(file_path)
        self._temporary_files.append(file_path)
        with open(file_path, 'w') as s:
            s.write(data)

    def _read_temporary_file(self, file_path):
        file_path = os.path.join(self.main_folder, file_path)
        with open(file_path, 'r') as s:
            return s.read()

    def _create_temporary_folder_if_necessary(self, path):
        path = os.path.join(self.main_folder, path)
        self._temporary_folders.append(path)
        if not os.path.exists(path):
            os.mkdir(path)
        else:
            assert os.path.isdir(path), 'Oops! "%s" is not a folder.' % path

    def _exists_temporary_file_or_folder(self, path):
        path = os.path.join(self.main_folder, path)
        return os.path.exists(path)

    def _delete_temporary_files_and_folders(self):
        for file in self._temporary_files:
            if os.path.exists(file):
                os.remove(file)
        self._temporary_files = []

        for folder in self._temporary_folders:
            if os.path.exists(folder):
                assert folder != 'scriptcraft'
                shutil.rmtree(folder)
        self._temporary_folders = []
