#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest

from scriptcraft import direction
from scriptcraft.parser import Parser, parse_system_question
from scriptcraft.utils import *



class BaseParsingTestCase(unittest.TestCase):
    class SimpleCommand(object):
        COMMAND_NAMES = ('simple', 's')
        ARGUMENTS = ()
        @staticmethod
        def CONSTRUCTOR():
            return '<simple command>'

    class IntegerCommand(object):
        COMMAND_NAMES = ('integer', 'i')
        ARGUMENTS = ('int',)
        @staticmethod
        def CONSTRUCTOR(i):
            return i

    class StringCommand(object):
        COMMAND_NAMES = ('string',)
        ARGUMENTS = ('str',)
        @staticmethod
        def CONSTRUCTOR(s):
            return s

    class DirectionCommand(object):
        COMMAND_NAMES = ('direction', 'd')
        ARGUMENTS = ('direction',)
        @staticmethod
        def CONSTRUCTOR(d):
            return d

    class ComplexCommand(object):
        COMMAND_NAMES = ('complex', 'c')
        ARGUMENTS = ('int', 'str', 'direction')
        @staticmethod
        def CONSTRUCTOR(i, s, d):
            return (i, s, d)

    ALL_COMMANDS = (SimpleCommand,
                    IntegerCommand,
                    StringCommand,
                    DirectionCommand,
                    ComplexCommand)

    def setUp(self):
        self.p = Parser(BaseParsingTestCase.ALL_COMMANDS)

    def parse_text(self, input_text):
        self.message_stubs, self.commands = self.p.parse(input_text)

    def assert_no_messages(self):
        self.assertEqual(self.message_stubs, [])

    def assert_no_command(self):
        self.assertEqual(self.commands, [])

    def assert_command_is(self, command):
        self.assertEqual(self.commands, [command])


class TestBasicParsing(BaseParsingTestCase):
    def test_empty_text(self):
        self.parse_text("")
        self.assert_no_messages()
        self.assert_no_command()

    def test_simple_command(self):
        self.parse_text("SIMPLE")
        self.assert_no_messages()
        self.assert_command_is('<simple command>')

    def test_integer_command(self):
        self.parse_text("INTEGER -12345678")
        self.assert_no_messages()
        self.assert_command_is(-12345678)

    def test_string_command(self):
        string = "x"*256
        self.parse_text("STRING \t" + string + " ")
        self.assert_no_messages()
        self.assert_command_is(string)

    def test_direction_command(self):
        self.parse_text("D N")
        self.assert_no_messages()
        self.assert_command_is(direction.N)

    def test_messages(self):
        self.parse_text((u'1 simple message\n'
                         u'-2 valid message receiver\n'
                         u'3\n'
                         u'1234 \n'
                         u'2345\t\n'
                         u'3456  \r\t\n'
                         u'7 zażółć gęślą jaźń'))
        self.assertEqual(self.message_stubs,
                          [(1, u'simple message'),
                           (-2, u'valid message receiver'),
                           (3, u''),
                           (1234, u''),
                           (2345, u''),
                           (3456, u' \r\t'),
                           (7, u'zażółć gęślą jaźń')])
        self.assert_no_command()

    def test_whitespaces(self):
        self.parse_text("\t\r\n\rCOMPLEX\t \r777 string\t  S\n\n")
        self.assert_no_messages()
        self.assert_command_is((777, 'string', direction.S))

    def test_case_insensitive(self):
        self.parse_text("cOmpLex 5 sTrInG e")
        self.assert_no_messages()
        self.assert_command_is((5, 'sTrInG', direction.E))


class TestParsingInvalidData(BaseParsingTestCase):
    def test_too_long_int(self):
        self.parse_text("INTEGER 1234567890")
        self.assert_no_messages()
        self.assert_no_command()

    def test_too_long_string(self):
        self.parse_text("STRING "+"x"*257)
        self.assert_no_messages()
        self.assert_no_command()


class TestParsingAmbiguousCommands(unittest.TestCase):
    def test(self):
        """ Test detecting ambiguous situation. Here: two commands
        have the same name ('collision') with one argument. """

        class A(object):
            COMMAND_NAMES = ('a', 'collision')
            ARGUMENTS = ('int',)
            CONSTRUCTOR = lambda x: x

        class B(object):
            COMMAND_NAMES = ('b', 'collision')
            ARGUMENTS = ('direction',)
            CONSTRUCTOR = lambda x: x

        illegal_operation = lambda: Parser([A, B])
        self.assertRaises(ValueError, illegal_operation)


class TestParsingSystemQuestions(unittest.TestCase):
    def test_parsing_list_units_command(self):
        answer = parse_system_question('list units')
        expected_answer = ('list-units', ())
        self.assertEqual(answer, expected_answer)

    def test_parsing_lu_command(self):
        answer = parse_system_question('lu')
        expected_answer = ('list-units', ())
        self.assertEqual(answer, expected_answer)

    def test_parsing_unit_info_command(self):
        answer = parse_system_question('unit 3')
        expected_answer = ('unit-info', (3,))
        self.assertEqual(answer, expected_answer)

    def test_parsing_u_command(self):
        answer = parse_system_question('u 123')
        expected_answer = ('unit-info', (123,))
        self.assertEqual(answer, expected_answer)

    def test_parsing_blank_input(self):
        answer = parse_system_question('')
        expected_answer = ('error', ())
        self.assertEqual(answer, expected_answer)

    def test_whitespaces(self):
        answer = parse_system_question('  list\tunits\r')
        expected_answer = ('list-units', ())
        self.assertEqual(answer, expected_answer)

    def test_case_insensitive(self):
        answer = parse_system_question('lIsT UNITS')
        expected_answer = ('list-units', ())
        self.assertEqual(answer, expected_answer)


class TestParsingEfficiency(BaseParsingTestCase):
    @max_time(1)
    def test_parsing_long_messages(self):
        self.parse_text(('5 ' + 'ab jh\t @6'*100 + '\n')*20)

    @max_time(75)
    def test_parsing_a_lot_of_messages(self):
        self.parse_text('5\n'*5000)

    @max_time(150)
    def test_parsing_a_lot_of_commands(self):
        self.parse_text('S\n'*5000)

    @max_time(30)
    def test_parsing_invalid_data(self):
        self.parse_text(('INTEGER ' + '1 '*500 + '\n' +
                         ' s \n'*1000))

    @max_time(10)
    def test_parsing_blank_input(self):
        self.parse_text('  \t \n'*2500)


