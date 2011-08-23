#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from utils import *

from scparser import Parser
from message import Message
import cmds
import direction
import units


class TestSCParser(unittest.TestCase):

	def test_basic(self):
		p = Parser("", 2)
		self.assertEqual(p.messages, [])
		self.assertEqual(p.commands, [])
		self.assertEqual(p.invalid_lines_numbers, [])
				
		
		
	def test_stop_command(self):
		p = Parser("STOP", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.StopCommand()])	

	def test_move_command(self):
		p = Parser("MOVE N", 2)
		self.assertEqual(p.invalid_lines_numbers, [])		
		self.assertEqual(p.commands, [cmds.MoveCommand(direction.N)])	
		
	def test_complex_move_command(self):
		p = Parser("MOVE 2 3", 2)
		self.assertEqual(p.invalid_lines_numbers, [])				
		self.assertEqual(p.commands, [cmds.ComplexMoveCommand((2,3))])
		
	def test_complex_gather_command(self):
		p = Parser("GATHER 4 13", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.ComplexGatherCommand((4,13))])
		
	def test_complex_attack_command(self):
		p = Parser("ATTACK 9 2", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.ComplexAttackCommand((9,2))])
		
	def test_fire_command(self):
		p = Parser("FIRE 5 6", 2)
		self.assertEqual(p.invalid_lines_numbers, [])	
		self.assertEqual(p.commands, [cmds.FireCommand((5,6))])

	def test_build_command(self):
		p = Parser("BUILD TANK", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.BuildCommand(units.TANK_TYPE_ID)])



	def test_lower_direction(self):
		p = Parser("MOVE e", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])	
		
	def test_unit_type_by_ID(self):
		p = Parser("BUILD 5", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.BuildCommand(units.MINER_TYPE_ID)])
		
	def test_unit_type_by_short_name(self):
		p = Parser("BUILD B", 2)
		self.assertEqual(p.invalid_lines_numbers, [])	
		self.assertEqual(p.commands, [cmds.BuildCommand(units.BASE_TYPE_ID)])	
		
	def test_command_by_short_name(self):
		p = Parser("M s", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.MoveCommand(direction.S)])	
		
	def test_empty_lines(self):
		p = Parser("MOVE e\n\nMOVE n", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [
			cmds.MoveCommand(direction.E),
			cmds.MoveCommand(direction.N),
		])		
		
	def test_lower_command(self):
		p = Parser("move E", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])
				
	def test_whitespaces(self):
		p = Parser("\t\n\r  \tMOVE e\t\n", 2)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])
		
		
		
	def test_messages(self):
		p = Parser("5 wiadomosc do wyslania", 123)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.messages, [Message(123, 5, 'wiadomosc do wyslania')])
		
	def test_message_coding(self):
		p = Parser("0 zażółć gęślą jaźń", 123)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.messages, [Message(123, 0, 'zażółć gęślą jaźń')])	
		
	def test_message_whitespaces(self):
		p = Parser("12\t b\rw", 123)
		self.assertEqual(p.invalid_lines_numbers, [])		
		self.assertEqual(p.messages, [Message(123, 12, ' b\rw')])
		
	def test_empty_message(self):
		p = Parser("12", 123)
		self.assertEqual(p.invalid_lines_numbers, [])
		self.assertEqual(p.messages, [Message(123, 12, '')])

		
		
	
	def test_parse_invalid_command(self):
		p = Parser("\n MO 3 \nM 3\n", 2)
		self.assertEqual(p.invalid_lines_numbers, [2, 3])
		self.assertEqual(p.commands, [])

		
		
		
class TestEfficiencyParsingMessages(unittest.TestCase):
	def setUp(self):
		self.input_data = ('5 ' + 'ab jh\t @6'*100 + '\n')*20

	@ max_time(1)
	def test(self):
		p = Parser(self.input_data, 2)
		
class TestEfficiencyParsingCommands(unittest.TestCase):
	def setUp(self):
		self.input_data = ('  MOVE 6\t4\n')*1000

	@ max_time(1)
	def test(self):
		p = Parser(self.input_data, 2)
		
class TestEfficiencyParsingInvalidInput(unittest.TestCase):
	def setUp(self):
		self.input_data = 'MOVE ' + '1 '*500 + '\n' \
			+ ' s \n'*1000

	@ max_time(1)
	def test(self):
		p = Parser(self.input_data, 2)

class TestEfficiencyParsingBlankInput(unittest.TestCase):
	def setUp(self):
		self.input_data = '  \t \n'*2500

	@ max_time(1)
	def test(self):
		p = Parser(self.input_data, 2)
		
		
if __name__ == '__main__':
	unittest.main()
	
	
