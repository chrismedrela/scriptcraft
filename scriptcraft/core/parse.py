#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft.core import direction, cmds



#-------------------------------------------------------- some usefull functions

def _parse_as_int(data):
    """ Return int or None if data is invalid. """

    if len(data)>8:
        return None
    try:
        return int(data)
    except ValueError:
        return None


def _parse_as_direction(data):
    """ Return direction.* or None if data is invalid. """

    try:
        return direction.BY_NAME[data.upper()]
    except KeyError:
        return None


def _parse_as_str(data, max_string_length=256):
    """ Return data or None if data has more characters than max_string_length
    argument (default 256). """

    if len(data) > max_string_length:
        return None
    return data


def _split_to_word_and_rest(line):
    splited_line = line.split(None, 1)
    command = splited_line[0]
    rest = splited_line[1] if len(splited_line) >= 2 else ''
    return command, rest



#----------------------------------------------------------------------- globals
# _COMMANDS = {
#    <name of command> : {
#        <number of args> :
#            (    <signature>,
#                <function returning (cmds.*Command)>,
#            )
#    }
# }

_COMMANDS = {}

_COMMANDS['STOP'] = _COMMANDS['S'] = {
    0 : (
            (_parse_as_int,),
            lambda : cmds.StopCommand(),
        ),
}
_COMMANDS['MOVE'] = _COMMANDS['M'] = {
    1 : (
            (_parse_as_direction,),
            lambda direction: cmds.MoveCommand(direction=direction),
        ),
    2 : (
            (_parse_as_int, _parse_as_int),
            lambda x, y: cmds.ComplexMoveCommand(destination=(x,y)),
        ),
}
_COMMANDS['GATHER'] = _COMMANDS['G'] = {
    2 : (
            (_parse_as_int, _parse_as_int),
            lambda x, y: cmds.ComplexGatherCommand(destination=(x,y)),
        ),
}
_COMMANDS['FIRE'] = _COMMANDS['F'] = {
    2 : (
            (_parse_as_int, _parse_as_int),
            lambda x, y: cmds.FireCommand(destination=(x,y)),
        ),
}
_COMMANDS['ATTACK'] = _COMMANDS['A'] = {
    2 : (
            (_parse_as_int, _parse_as_int),
            lambda x, y: cmds.ComplexAttackCommand(destination=(x,y)),
        ),
}
_COMMANDS['BUILD'] = _COMMANDS['B'] = {
    1 : (
            (_parse_as_str,),
            lambda type_name: cmds.BuildCommand(unit_type_name=type_name.lower()),
        ),
}


class Parse (object):
    """
    Arguments of __init__:
     input_data -- data that should be parsed (many lines allowed)

    Data are parsed in __init__. After it some attributes are created:
     commands : list(cmds.*Command)
     message_stubs : list(tuple(receiver_ID, text_of_message))
     invalid_lines_numbers : list(int) -- the first line has no 1 (not 0!)

    """

    def __init__(self, input_data):
        self.message_stubs = []
        self.commands = []
        self.invalid_lines_numbers = []

        self._parse_input_data(input_data)

    def _parse_input_data(self, input_data):
        for line_index, line in enumerate(input_data.split('\n')):
            self._line_no = line_index+1

            # empty line?
            line = line.strip()
            if len(line) == 0:
                continue

            # command or message?
            command, rest_of_line = _split_to_word_and_rest(line)
            command_as_int = _parse_as_int(command)
            if command_as_int == None: # command
                self._parse_command(command, rest_of_line)
            else: # message
                message_text = line[len(command)+1:]
                receiver_ID = command_as_int
                message_stub = (receiver_ID, message_text)
                self.message_stubs.append(message_stub)

    def _parse_command(self, command_as_string, rest_of_line):
        command_as_string = command_as_string.upper()
        signatures_with_functions_by_number_of_args = _COMMANDS.get(command_as_string, None)
        if signatures_with_functions_by_number_of_args == None:
            self._invalid_line()
        else:
            args_of_command = rest_of_line.split()

            # check number of args
            signature_with_function = signatures_with_functions_by_number_of_args.get(len(args_of_command), None)
            if signature_with_function == None:
                self._invalid_line()
                return
            signature, method = signature_with_function

            # convert args
            args = []
            for function, arg in zip(signature, args_of_command):
                result = function(arg)
                if result == None:
                    self._invalid_line()
                    return
                args.append(result)

            command = method(*args)
            self.commands.append(command)

    def _invalid_line(self):
        self.invalid_lines_numbers.append(self._line_no)
