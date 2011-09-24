#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from utils import *

from Field import Field

class TestField(unittest.TestCase):
    def test_trees(self):
        field = Field(trees=True)
        self.assertEqual(field.is_empty(), False)
        self.assertEqual(field.has_trees(), True)
        self.assertEqual(field.has_unit(), False)
        
    def test_unit(self):
        field = Field(unit_ID=667)
        self.assertEqual(field.is_empty(), False)
        self.assertEqual(field.has_trees(), False)
        self.assertEqual(field.has_unit(), True)
        self.assertEqual(field.get_unit_ID(), 667)
        
    def test_minerals(self):
        field = Field(minerals=0)
        self.assertEqual(field.is_empty(), False)        
        self.assertEqual(field.has_mineral_deposit(), True)
        self.assertEqual(field.has_trees(), False)
        self.assertEqual(field.get_minerals(), 0)
        
    def test_trees_and_unit(self):
        self.assertRaises(
            ValueError,
            lambda: Field(trees=True, unit_ID=1)
        )
        
    def test_erased_field(self):
        field = Field(trees=True)
        field = field.Erased()
        self.assertEqual(field.is_empty(), True)
        self.assertEqual(field.has_trees(), False)
        
    def test_place_on_occupied_field_allowed(self):
        field = Field(minerals=2)
        field = field.PlacedTrees()
        
    def test_repr(self):
        field = Field(upland=True, unit_ID=123)
        self.assertEqual(repr(field), '<Field(type=2, arg=123) : upland with unit 123>')
                                
        
class TestEfficiency(unittest.TestCase):
    @ max_time(10)
    def test_function_is_empty(self):
        f = Field(minerals=2)
        for _ in xrange(64*64):
            f.is_empty()
    
    @ max_time(50)
    def test_constructor_placed_minerals(self):
        f = Field(trees=True)
        for _ in xrange(64*64):
            f.PlacedMinerals(123)   
        
if __name__ == '__main__':
    unittest.main()
    
