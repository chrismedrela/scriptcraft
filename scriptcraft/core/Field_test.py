#!/usr/bin/env python
#-*- coding:utf-8 -*-

from copy import deepcopy
import unittest

from scriptcraft.core.Field import Field
from scriptcraft.utils import *



class TestField(unittest.TestCase):
    def test_trees(self):
        field = Field(trees=True)

        self.assertFalse(field.is_empty())
        self.assertFalse(field.is_flat_and_empty())
        self.assertTrue(field.has_trees())
        self.assertFalse(field.has_unit())

    def test_unit(self):
        field = Field(unit_ID=667)

        self.assertFalse(field.is_empty())
        self.assertFalse(field.has_trees())
        self.assertTrue(field.has_unit())
        self.assertEqual(field.get_unit_ID(), 667)

    def test_minerals_and_flat(self):
        field = Field(minerals=0)

        self.assertFalse(field.is_empty())
        self.assertTrue(field.is_flat())
        self.assertTrue(field.has_mineral_deposit())
        self.assertFalse(field.has_trees())
        self.assertEqual(field.get_minerals(), 0)

    def test_trees_and_unit(self):
        self.assertRaises(
            ValueError,
            lambda: Field(trees=True, unit_ID=1)
        )

    def test_erased_field(self):
        field = Field(trees=True)
        field = field.Erased()

        self.assertTrue(field.is_empty())
        self.assertTrue(field.is_flat_and_empty())
        self.assertFalse(field.has_trees())

    def test_placed_unit(self):
        field = Field(trees=True)
        field = field.PlacedUnit(unit_ID=123)

        self.assertFalse(field.has_trees())
        self.assertEqual(field.get_unit_ID(), 123)

    def test_place_on_occupied_field_allowed(self):
        field = Field(minerals=2)
        field = field.PlacedTrees()

    def test_repr(self):
        field = Field(upland=True, unit_ID=123)

        self.assertEqual(repr(field),
                         '<Field(type=2, arg=123) : upland with unit 123>')

    def test_deep_copy(self):
        field = Field(unit_ID=123)
        field_copy = deepcopy(field)
        self.assertEqual(field, field_copy)


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
