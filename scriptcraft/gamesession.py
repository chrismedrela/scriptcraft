#!/usr/bin/env python
#-*- coding:utf-8 -*-


import ConfigParser
try:
    import cPickle as pickle
except:
    import pickle
import os

from scriptcraft.compilation import CompileAndRunProgram
from scriptcraft.gamestate import Language



class LanguageConfiguration(object):
    def __init__(self, source_file_name, binary_file_name,
                 compilation_command, running_command):
        self.source_file_name = source_file_name
        self.binary_file_name = binary_file_name
        self.compilation_command = compilation_command
        self.running_command = running_command


class SystemConfiguration(object):
    SECTION_TO_LANGUAGE = {
        'cpp' : Language.CPP,
        'python' : Language.PYTHON,
    }

    def __init__(self, ini_file):
        """ May raise IOError or ConfigParser.Error or ValueError. """
        self.languages_configurations = {}

        config = ConfigParser.RawConfigParser()
        config.readfp(open(ini_file))
        sections = config.sections()

        if not config.has_option('DEFAULT', 'compilationlimit'):
            raise ValueError("Missing 'compilationlimit' option "
                             "in default section.")
        if not config.has_option('DEFAULT', 'executinglimit'):
            raise ValueError("Missing, 'executinglimit' option "
                             "in default section.")
        self.max_compilation_time = \
          config.getfloat('DEFAULT', 'compilationlimit')
        if self.max_compilation_time == 0.0:
            self.max_compilation_time = None
        self.max_execution_time = \
          config.getfloat('DEFAULT', 'executinglimit')
        if self.max_execution_time == 0.0:
            self.max_execution_time = None

        for section in sections:
            language = SystemConfiguration.SECTION_TO_LANGUAGE.get(
                section.lower(), None)
            if language is None:
                raise ValueError('Unknown language name %r.' % section)
            if (not config.has_option(section, 'sourceextension') or
                not config.has_option(section, 'binaryextension') or
                not config.has_option(section, 'compile') or
                not config.has_option(section, 'execute')):
                raise ValueError("Missing fields in section %r. "
                                 "The section should contain: "
                                 "'sourceextension', 'binaryextension' "
                                 "'compile' and 'execute'." % section)
            source_extension = config.get(section, 'sourceextension')
            binary_extension = config.get(section, 'binaryextension')
            compile_command = config.get(section, 'compile')
            execute_command = config.get(section, 'execute')
            self.languages_configurations[language] = LanguageConfiguration(
                'src.'+source_extension, 'bin.'+binary_extension,
                compile_command, execute_command)


class GameSession(object):
    GAME_FILE_PATH = 'game.gam'
    PICKLE_PROTOCOL = 2

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
        pickle.dump(self.game, open(self._game_file, 'w'),
                    GameSession.PICKLE_PROTOCOL)

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
            running_commands,
            self._system_configuration.max_compilation_time,
            self._system_configuration.max_execution_time)
        self.game.tic(compile_and_run)

    def __getattr__(self, name):
        return getattr(self.game, name)

    @property
    def _game_file(self):
        return os.path.join(self._directory, GameSession.GAME_FILE_PATH)
