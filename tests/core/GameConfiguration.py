#!/usr/bin/env python
#-*- coding:utf-8 -*-

from copy import deepcopy
import unittest

from scriptcraft.core.GameConfiguration import GameConfiguration
from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED
from scriptcraft.utils import *



class TestGameConfiguration(unittest.TestCase):
    def setUp(self):
        self._create_unit_types()

        self.kwargs = {'units_types':self.unit_types,
                       'main_base_type':self.miner_type,
                       'main_miner_type':self.miner_type,
                       'minerals_for_main_unit_at_start':10,
                       'probability_of_mineral_deposit_growing':0.1,
                       'languages':()}

    def _create_unit_types(self):
        kwargs = {'attack_range':0,
                  'vision_radius':7,
                  'storage_size':1,
                  'build_cost':3,
                  'can_build':False,
                  'movable':True,
                  'behaviour_when_attacked':BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                  'names':('5', 'miner', 'm')}
        self.miner_type = UnitType(**kwargs)

        kwargs['names'] = ('7', 'superminer', 'm')
        self.second_miner_type = UnitType(**kwargs)

        self.unit_types = [self.miner_type]

    def test_unit_types_must_have_unique_names(self):
        self.kwargs['units_types'] = [self.miner_type,
                                      self.second_miner_type]

        self._test_game_configuration_cannot_be_created()

    def test_main_base_type_must_be_in_units_types(self):
        self.kwargs['units_types'] = [self.second_miner_type]
        self.kwargs['main_base_type'] = self.miner_type

        self._test_game_configuration_cannot_be_created()

    def test_deep_copy(self):
        configuration = GameConfiguration(**self.kwargs)
        configuration_copy = deepcopy(configuration)
        self.assertEqual(configuration, configuration_copy)

    def _test_game_configuration_cannot_be_created(self):
        illegal_operation = lambda: GameConfiguration(**self.kwargs)
        self.assertRaises(ValueError, illegal_operation)
