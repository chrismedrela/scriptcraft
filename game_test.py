#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import game

def skip(_=''):
	return lambda x: None

class TestField(unittest.TestCase):
	def test_is_empty(self):
		self.assertTrue(game.new_field())

class TestParseLine(unittest.TestCase):
	def test_basic(self):
		self.assertEqual(game.parse_line('3 n ala', ['int', 'dir', 'str']), (3, game.DIRECTION_N, 'ala'))

class TestGameMap(unittest.TestCase):
	""" Testuje klasę GameMap """
	def setUp(self):
		self.game_map = game.GameMap(size=8, start_positions=[(2,3)])
				
	def tearDown(self):
		pass
		
	def test_getting_fields(self):
		self.game_map[0][0]
		
	def test_exists_free_start_positions(self):
		self.assertTrue(self.game_map.exists_free_flat_start_position())

class TestGame(unittest.TestCase):
	""" Testuje klasę Game """
	def setUp(self):
		self.player = game.Player(name='player1', program_code='print "MOVE N"')
		self.game = game.Game(game_map=game.GameMap(size=8, start_positions=[(2,2),(3,2),(4,2)]), players=[self.player])
				
	def tearDown(self):
		pass
		
	def test_add_player(self):
		self.game.add_player(game.Player(name='player2', program_code=''))
		self.assertEqual(len(self.game._players_by_ID), 2)
		
	def test_set_program_code(self):
		new_program_code = 'print "MOVE S"'
		self.game.set_program_code(self.player.ID, new_program_code)
		self.assertEqual(self.game._players_by_ID[self.player.ID].program_code, new_program_code)
		
	@skip()
	def test_tic(self):
		self.game.add_object
		self.game.tic()
