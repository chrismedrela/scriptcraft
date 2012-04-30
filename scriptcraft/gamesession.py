#!/usr/bin/env python
#-*- coding:utf-8 -*-


try:
    import cPickle as pickle
except:
    import pickle
import os

from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.Language import Language


class SystemConfiguration(object):
    pass


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
        compile_and_run = CompileAndRunProgram(
            self._directory,
            {Language.CPP:'src.cpp',
             Language.PYTHON:'src.py'},
            {Language.CPP:'bin.exe',
             Language.PYTHON:'bin.py'},
            {Language.CPP:'g++ src.cpp -o bin.exe',
             Language.PYTHON:'cp src.py bin.py'},
            {Language.CPP:'./bin.exe',
             Language.PYTHON:'python bin.py'}
        )
        self.game.tic(compile_and_run)

    def __getattr__(self, name):
        return getattr(self.game, name)

    @property
    def _game_file(self):
        return os.path.join(self._directory, GameSession.GAME_FILE_PATH)
