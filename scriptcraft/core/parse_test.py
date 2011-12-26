#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft.core import cmds, direction
from scriptcraft.core.Message import Message
from scriptcraft.core.parse import Parse
from scriptcraft.utils import *


class TestBasicParsing(unittest.TestCase):

    def test_basic(self):
        p = Parse("", 2)
        self.assertEqual(p.messages, [])
        self.assertEqual(p.commands, [])
        self.assertEqual(p.invalid_lines_numbers, [])


    def test_stop_command(self):
        self.p = Parse("STOP", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.StopCommand())


    def test_move_command(self):
        self.p = Parse("MOVE N", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.N))


    def test_complex_move_command(self):
        self.p = Parse("MOVE 2 3", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexMoveCommand((2,3)))


    def test_complex_gather_command(self):
        self.p = Parse("GATHER 4 13", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexGatherCommand((4,13)))


    def test_complex_attack_command(self):
        self.p = Parse("ATTACK 9 2", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.ComplexAttackCommand((9,2)))


    def test_fire_command(self):
        self.p = Parse("FIRE 5 6", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.FireCommand((5,6)))


    def test_build_command(self):
        self.p = Parse("BUILD TANK", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.BuildCommand("tank"))


    def _test_no_invalid_lines_and_command_equal_to(self, command):
        self.assertEqual(self.p.invalid_lines_numbers, [])
        self.assertEqual(self.p.commands, [command])



class TestDetailsOfParsing(unittest.TestCase):

    def test_lower_direction(self):
        self.p = Parse("MOVE e", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))


    def test_command_by_short_name(self):
        self.p = Parse("M s", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.S))


    def test_empty_lines(self):
        p = Parse("MOVE e\n\nMOVE n", 2)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.commands, [cmds.MoveCommand(direction.E),
                                      cmds.MoveCommand(direction.N)])


    def test_lower_command(self):
        self.p = Parse("move E", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))


    def test_whitespaces(self):
        self.p = Parse("\t\n\r  \tMOVE e\t\n", 2)
        self._test_no_invalid_lines_and_command_equal_to(cmds.MoveCommand(direction.E))


    def test_parse_invalid_command(self):
        self.p = Parse("\n MO 3 \nM 3\n", 2)
        self._test_invalid_lines_and_no_command([2, 3])


    def test_parse_too_long_int_and_str(self):
        self.p = Parse("MOVE 30000000000 300000000000\nBUILD "+"T"*10000, 3)
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
                           Message(123, 5, 'message text'))


    def test_message_coding(self):
        self._test_message(u"0 zażółć gęślą jaźń",
                           Message(123, 0, u'zażółć gęślą jaźń'))


    def test_message_whitespaces(self):
        self._test_message(u"12\t b\rw",
                           Message(123, 12, ' b\rw'))


    def test_empty_message(self):
        self._test_message(u"12",
                           Message(123, 12, ''))


    def _test_message(self, text, message, sender=123):
        p = Parse(text, sender)
        self.assertEqual(p.invalid_lines_numbers, [])
        self.assertEqual(p.messages, [message])



class TestEfficiencyParsingLongMessages(unittest.TestCase):

    def setUp(self):
        self.input_data = ('5 ' + 'ab jh\t @6'*100 + '\n')*20


    @ max_time(1)
    def test(self):
        Parse(self.input_data, 2)



class TestEfficiencyParsingManyMessages(unittest.TestCase):

    def setUp(self):
        self.input_data = '5\n'*5000


    @ max_time(75)
    def test(self):
        Parse(self.input_data, 2)



class TestEfficiencyParsingCommands(unittest.TestCase):

    def setUp(self):
        self.input_data = ('S\n')*5000


    @ max_time(150)
    def test(self):
        Parse(self.input_data, 2)



class TestEfficiencyParsingInvalidInput(unittest.TestCase):

    def setUp(self):
        self.input_data = 'MOVE ' + '1 '*500 + '\n' \
            + ' s \n'*1000


    @ max_time(30)
    def test(self):
        Parse(self.input_data, 2)



class TestEfficiencyParsingBlankInput(unittest.TestCase):

    def setUp(self):
        self.input_data = '  \t \n'*2500


    @ max_time(10)
    def test(self):
        Parse(self.input_data, 2)





if __name__ == '__main__':
    unittest.main()


