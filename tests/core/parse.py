#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.core import cmds, direction
from scriptcraft.core.parse import Parse
from scriptcraft.utils import *



class TestBasicParsing(unittest.TestCase):
    def test_basic(self):
        p = Parse("")
        self.assertEqual(p.message_stubs, [])
        self.assertEqual(p.commands, [])
        self.assertEqual(p.invalid_lines_numbers, [])

    def test_stop_command(self):
        self.p = Parse("STOP")
        self._test_no_invalid_lines_and_command_equal_to(cmds.StopCommand())

    def test_move_command(self):
        self.p = Parse("MOVE N")
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.N))

    def test_complex_move_command(self):
        self.p = Parse("MOVE 2 3")
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexMoveCommand((2,3)))

    def test_complex_gather_command(self):
        self.p = Parse("GATHER 4 13")
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexGatherCommand((4,13)))

    def test_complex_attack_command(self):
        self.p = Parse("ATTACK 9 2")
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexAttackCommand((9,2)))

    def test_fire_command(self):
        self.p = Parse("FIRE 5 6")
        self._test_no_invalid_lines_and_command_equal_to(cmds.FireCommand((5,6)))

    def test_build_command(self):
        self.p = Parse("BUILD TANK")
        self._test_no_invalid_lines_and_command_equal_to(cmds.BuildCommand("tank"))

    def _test_no_invalid_lines_and_command_equal_to(self, command):
        self.assertEqual(self.p.invalid_lines_numbers, [])
        self.assertEqual(self.p.commands, [command])


class TestDetailsOfParsing(unittest.TestCase):
    def test_lower_direction(self):
        self.p = Parse("MOVE e")
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))

    def test_command_by_short_name(self):
        self.p = Parse("M s")
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.S))

    def test_empty_lines(self):
        p = Parse("MOVE e\n\nMOVE n")
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.E),
                                      cmds.MoveCommand(direction.N)])

    def test_lower_command(self):
        self.p = Parse("move E")
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))

    def test_whitespaces(self):
        self.p = Parse("\t\n\r  \tMOVE e\t\n")
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))

    def test_parse_invalid_command(self):
        self.p = Parse("\n MO 3 \nM 3\n")
        self._test_invalid_lines_and_no_command([2, 3])

    def test_parse_too_long_int_and_str(self):
        self.p = Parse("MOVE 30000000000 300000000000\nBUILD "+"T"*10000)
        self._test_invalid_lines_and_no_command([1, 2])

    def _test_invalid_lines_and_no_command(self, invalid_lines):
        self.assertEqual(self.p.invalid_lines_numbers, invalid_lines)
        self.assertEqual(self.p.commands, [])

    def _test_no_invalid_lines_and_command_equal_to(self, command):
        self.assertEqual(self.p.invalid_lines_numbers, [])
        self.assertEqual(self.p.commands, [command])


class TestMessages(unittest.TestCase):
    def test_messages(self):
        self._test_message(u"5 message text",
                           (5, 'message text'))

    def test_message_coding(self):
        self._test_message(u"0 zażółć gęślą jaźń",
                           (0, u'zażółć gęślą jaźń'))

    def test_message_whitespaces(self):
        self._test_message(u"12\t b\rw",
                           (12, ' b\rw'))

    def test_empty_message(self):
        self._test_message(u"12",
                           (12, ''))

    def _test_message(self, text, message):
        p = Parse(text)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.message_stubs, [message])


class TestEfficiencyParsingLongMessages(unittest.TestCase):
    def setUp(self):
        self.input_data = ('5 ' + 'ab jh\t @6'*100 + '\n')*20

    @ max_time(1)
    def test(self):
        Parse(self.input_data)


class TestEfficiencyParsingManyMessages(unittest.TestCase):
    def setUp(self):
        self.input_data = '5\n'*5000

    @ max_time(75)
    def test(self):
        Parse(self.input_data)


class TestEfficiencyParsingCommands(unittest.TestCase):
    def setUp(self):
        self.input_data = ('S\n')*5000

    @ max_time(150)
    def test(self):
        Parse(self.input_data)


class TestEfficiencyParsingInvalidInput(unittest.TestCase):
    def setUp(self):
        self.input_data = 'MOVE ' + '1 '*500 + '\n' \
            + ' s \n'*1000

    @ max_time(30)
    def test(self):
        Parse(self.input_data)


class TestEfficiencyParsingBlankInput(unittest.TestCase):
    def setUp(self):
        self.input_data = '  \t \n'*2500

    @ max_time(10)
    def test(self):
        Parse(self.input_data)
