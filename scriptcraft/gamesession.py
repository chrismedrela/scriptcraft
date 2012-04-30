#!/usr/bin/env python
#-*- coding:utf-8 -*-


try:
    import cPickle as pickle
except:
    import pickle
import os

from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.Language import Language



class LanguageConfiguration(object):
    def __init__(self, source_file_name, binary_file_name,
                 compilation_command, running_command):
        self.source_file_name = source_file_name
        self.binary_file_name = binary_file_name
        self.compilation_command = compilation_command
        self.running_command = running_command


class SystemConfiguration(object):
    def __init__(self):
        self.languages_configurations = {
            Language.PYTHON : LanguageConfiguration(
                'src.py', 'bin.py',
                'cp src.py bin.py',
                'python bin.py'),
            Language.CPP : LanguageConfiguration(
                'src.cpp', 'bin',
                'g++ src.cpp -o bin',
                './bin')
        }


class GameSession(object):
    GAME_FILE_PATH = 'game.gam'

    def __init__(self, directory, system_configuration, game=None):
        """ May raise IOError or pickle.UnpicklingError. """
        self._directory = directory
        self._system_configuration = system_configuration
        if game:
            self.game = game
        else:
            self.game = pickle.load(open(self._game_file, 'r'))

    def save(self):
        """ Save game. May raise errors. """
        pickle.dump(self.game, open(self._game_file, 'w'))

    def tic(self):
        languages = self._system_configuration.languages_configurations.items()
        source_file_names = dict([(k, v.source_file_name) for k, v in languages])
        binary_file_names = dict([(k, v.binary_file_name) for k, v in languages])
        compilation_commands = dict([(k, v.compilation_command) for i in languages])
        running_commands = dict([(k, v.running_command) for i in languages])
        compile_and_run = CompileAndRunProgram(
            self._directory,
            source_file_names,
            binary_file_names,
            compilation_commands,
            running_commands)
        self.game.tic(compile_and_run)

    def __getattr__(self, name):
        return getattr(self.game, name)

    @property
    def _game_file(self):
        return os.path.join(self._directory, GameSession.GAME_FILE_PATH)
