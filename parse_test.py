#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from utils import *

from parse import Parse
from message import Message
import cmds
import direction
import units


class TestParse(unittest.TestCase):

    def test_basic(self):
        p = Parse("", 2)
        self.assertEqual(p.messages, [])
        self.assertEqual(p.commands, [])
        self.assertEqual(p.invalid_lines_numbers, [])



    def test_stop_command(self):
        p = Parse("STOP", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.StopCommand()])

    def test_move_command(self):
        p = Parse("MOVE N", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.N)])

    def test_complex_move_command(self):
        p = Parse("MOVE 2 3", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.ComplexMoveCommand((2,3))])

    def test_complex_gather_command(self):
        p = Parse("GATHER 4 13", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.ComplexGatherCommand((4,13))])

    def test_complex_attack_command(self):
        p = Parse("ATTACK 9 2", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.ComplexAttackCommand((9,2))])

    def test_fire_command(self):
        p = Parse("FIRE 5 6", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.FireCommand((5,6))])

    def test_build_command(self):
        p = Parse("BUILD TANK", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.BuildCommand("tank")])



    def test_lower_direction(self):
        p = Parse("MOVE e", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])

    def test_command_by_short_name(self):
        p = Parse("M s", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.S)])

    def test_empty_lines(self):
        p = Parse("MOVE e\n\nMOVE n", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [
            cmds.MoveCommand(direction.E),
            cmds.MoveCommand(direction.N),
        ])

    def test_lower_command(self):
        p = Parse("move E", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])

    def test_whitespaces(self):
        p = Parse("\t\n\r  \tMOVE e\t\n", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.E)])



    def test_messages(self):
        p = Parse("5 wiadomosc do wyslania", 123)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.messages, [Message(123, 5, 'wiadomosc do wyslania')])

    def test_message_coding(self):
        p = Parse("0 zażółć gęślą jaźń", 123)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.messages, [Message(123, 0, 'zażółć gęślą jaźń')])

    def test_message_whitespaces(self):
        p = Parse("12\t b\rw", 123)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.messages, [Message(123, 12, ' b\rw')])

    def test_empty_message(self):
        p = Parse("12", 123)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.messages, [Message(123, 12, '')])




    def test_parse_invalid_command(self):
        p = Parse("\n MO 3 \nM 3\n", 2)
        self.assertEqual(p.invalid_lines_numbers, [2, 3])
        self.assertEqual(p.commands, [])

    def test_parse_too_long_int_and_str(self):
        p = Parse("MOVE 30000000000 300000000000\nBUILD "+"T"*10000, 3)
        self.assertEqual(p.invalid_lines_numbers, [1, 2])
        self.assertEqual(p.commands, [])




class TestEfficiencyParsingLongMessages(unittest.TestCase):
    def setUp(self):
        self.input_data = ('5 ' + 'ab jh\t @6'*100 + '\n')*20

    @ max_time(1, repeat=3)
    def test(self):
        p = Parse(self.input_data, 2)

class TestEfficiencyParsingManyMessages(unittest.TestCase):
    def setUp(self):
        self.input_data = '5\n'*5000

    @ max_time(75, repeat=3)
    def test(self):
        p = Parse(self.input_data, 2)


class TestEfficiencyParsingCommands(unittest.TestCase):
    def setUp(self):
        self.input_data = ('S\n')*5000

    @ max_time(150, repeat=3)
    def test(self):
        p = Parse(self.input_data, 2)

class TestEfficiencyParsingInvalidInput(unittest.TestCase):
    def setUp(self):
        self.input_data = 'MOVE ' + '1 '*500 + '\n' \
            + ' s \n'*1000

    @ max_time(30, repeat=3)
    def test(self):
        p = Parse(self.input_data, 2)

class TestEfficiencyParsingBlankInput(unittest.TestCase):
    def setUp(self):
        self.input_data = '  \t \n'*2500

    @ max_time(10, repeat=3)
    def test(self):
        p = Parse(self.input_data, 2)


if __name__ == '__main__':
    unittest.main()


