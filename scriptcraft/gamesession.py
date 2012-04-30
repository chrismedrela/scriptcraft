#!/usr/bin/env python
#-*- coding:utf-8 -*-


try:
    import cPickle as pickle
except:
    import pickle
import os



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
        self.game.tic(self._directory)

    def __getattr__(self, name):
        return getattr(self.game, name)

    @property
    def _game_file(self):
        return os.path.join(self._directory, GameSession.GAME_FILE_PATH)
