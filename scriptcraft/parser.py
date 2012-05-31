#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft import direction
from scriptcraft.utils import *


def parse_system_question(question):
    """ Return tuple (command, args) where command is:

    - 'list-units' and then args is empty tuple; that's returned for
      questions like "LU" or "list units";

    - 'unit-info' and then args is tuple (unit_ID,); that's returned
      for questions like "U 3" or "unit 123";

    - 'error' and then args is empty_tuple; that's returned when the
      question is invalid

    """

    cleaned = question.lower().strip()
    split = tuple(cleaned.split(None, 1))

    if split == ('list', 'units') or split == ('lu',):
        return ('list-units', ())
    elif len(split)==2 and split[0] in ('unit', 'u'):
        maybe_unit_ID = _parse_int(split[1])
        if maybe_unit_ID is not None:
            return ('unit-info', (maybe_unit_ID,))
        else:
            return ('error', ())
    else:
        return ('error', ())


class Parser (object):
    def __init__(self, cmds):
        """
        Argument cmds is list of commands. Each command have the
        following attributes:

        COMMAND_NAMES -- list of names of the command (for example
        ['b', 'build']); command names are case-insensitive

        ARGUMENTS -- list of types where type is 'int', 'str' (max 256
        characters or 'direction'

        CONSTRUCTOR -- function that receives parsed arguments and
        return command

        """

        self._commands = {} # {(command_name, len(args)) : ([args_parsers], function)}
        for command in cmds:
            names = map(lambda x: x.upper(), command.COMMAND_NAMES)
            args = self._valid_arguments(command.ARGUMENTS)
            function = command.CONSTRUCTOR
            for name in names:
                key = (name, len(args))
                if key in self._commands:
                    raise ValueError(("Ambiguous commands: "
                                      "two commands '%s' with %d arguments."
                                      % (name, len(args))))
                self._commands[key] = (args, function)

    def _valid_arguments(self, args):
        for arg in args:
            if arg not in ('str', 'int', 'direction'):
                raise ValueError("Invalid argument type: '%s'" % arg)
        switch = {'str':_parse_str,
                  'int':_parse_int,
                  'direction':_parse_direction}
        return [switch[arg] for arg in args]

    @log_on_enter('parse', mode='only time')
    def parse(self, data):
        """
        This method returns tuple containing:
        commands -- list(cmds) where cmds are objects returned by
        CONSTRUCTOR function described in __init__ method; if the
        function returns None, the value is not in the list.
        message_stubs -- list(tuple(receiver_ID, text_of_message))

        """

        message_stubs = []
        commands = []

        for line in data.split('\n'):
            # empty line?
            striped_line = line.strip()
            if len(striped_line) == 0:
                continue

            # command or message?
            command, rest_of_line = self._split_to_word_and_rest(striped_line)
            command_as_int = _parse_int(command)
            if command_as_int is None: # that's a command
                command_as_string = command.upper()
                arguments = rest_of_line.split()
                key = (command_as_string, len(arguments))
                signature = self._commands.get(key, None)
                if signature is not None:
                    argument_converters, function = signature
                    arguments = [convert(arg) for (arg, convert)
                                 in zip(arguments, argument_converters)]
                    if None not in arguments: # so all arguments are valid
                        command = function(*arguments)
                        if command:
                            commands.append(command)
            else: # that's a message
                message_text = line[len(command)+1:]
                receiver_ID = command_as_int
                message_stub = (receiver_ID, message_text)
                message_stubs.append(message_stub)

        return (message_stubs, commands)

    def _split_to_word_and_rest(self, line):
        splited_line = line.split(None, 1)
        command = splited_line[0]
        rest = splited_line[1] if len(splited_line) >= 2 else ''
        return command, rest


def _parse_int(data):
    """ Return int or None if data is invalid. """

    if len(data)>9:
        return None
    try:
        return int(data)
    except ValueError:
        return None

def _parse_direction(data):
    """ Return direction.* or None if data is invalid. """

    try:
        return direction.BY_NAME[data.upper()]
    except KeyError:
        return None

def _parse_str(data, max_string_length=256):
    """ Return data or None if data has more characters than max_string_length
    argument (default 256). """

    if len(data) > max_string_length:
        return None
    return data

