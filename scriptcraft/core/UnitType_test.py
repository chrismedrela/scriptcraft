#!/usr/bin/env python
#-*- coding:utf-8 -*-


from copy import deepcopy
import unittest

from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED
from scriptcraft.utils import *



class TestUnitType(unittest.TestCase):

    def test_upper_cases_names(self):
        unit_type = self._build_simple_unit_type()
        self.assertEqual(unit_type.main_name, 'myunittype')


    def test_deep_copy(self):
        unit_type = self._build_simple_unit_type()
        unit_type_copy = deepcopy(unit_type)
        self.assertEqual(unit_type, unit_type_copy)


    def _build_simple_unit_type(self):
        result = UnitType(can_attack=False,
                          vision_radius=2,
                          has_storage=True,
                          storage_size=5,
                          build_cost=2,
                          can_build=False,
                          movable=False,
                          behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                          names=['MyUnitType', 'mut'])
        return result
