#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from message import Message
import direction
import cmds
import units
	

# -----------------------------------------------------------------------------
# globals 
# -----------------------------------------------------------------------------

_DIRECTIONS_BY_NAME = {
	'N' : direction.N,
	'E' : direction.E,
	'S' : direction.S,
	'W' : direction.W
}

_UNIT_TYPE_NAME_TO_TYPE_ID = {
	'TANK':units.TANK_TYPE_ID, 'T':units.TANK_TYPE_ID, '6':units.TANK_TYPE_ID,
	'MINER':units.MINER_TYPE_ID, 'M':units.MINER_TYPE_ID, '5':units.MINER_TYPE_ID,
	'BASE':units.BASE_TYPE_ID, 'B':units.BASE_TYPE_ID, '4':units.BASE_TYPE_ID,
}


def _parse_as_int(data):
	""" W przypadku niepowodzenia zwraca None """

	if len(data)>8:
		return None
	try:
		return int(data)
	except ValueError:
		return None

def _parse_as_direction(data):
	""" W przypadku niepowodzenia zwraca None w przeciwnym razie zwraca
	identyfikator kierunku świata (direction.W itp.). """

	try:
		return _DIRECTIONS_BY_NAME[data.upper()]
	except KeyError:
		return None

def _parse_as_str(data, max_string_length=256):
	""" W przypadku, gdy długość stringa przekracza max_string_length,
	zwraca None """

	if len(data) > max_string_length:
		return None
	return data

def _parse_as_object_type_name(data):
	""" Zwraca identyfikator typu jednostki lub None w przypadku
	niepowodzenia """

	type_name = _parse_as_str(data, max_string_length=16)
	type_ID = _UNIT_TYPE_NAME_TO_TYPE_ID.get(type_name, None)
	return type_ID


commands = {} # commands { <name of command> : { <number of args> : ( <signature>, <function returning (object_ID, *Command)> ) }}
commands['stop'] = commands['s'] = {
	0 : (
			(_parse_as_int,),
			lambda : cmds.StopCommand(),
		),
}
commands['move'] = commands['m'] = {
	1 : (
			(_parse_as_direction,),
			lambda direction: cmds.MoveCommand(direction=direction),
		),
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.ComplexMoveCommand(dest_pos=(x,y)),
		),
}
commands['gather'] = commands['g'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.ComplexGatherCommand(dest_pos=(x,y)),
		),
}
commands['fire'] = commands['f'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.FireCommand(dest_pos=(x,y)),
		),
}
commands['attack'] = commands['a'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.ComplexAttackCommand(dest_pos=(x,y)),
		),
}
commands['build'] = commands['b'] = {
	1 : (
			(_parse_as_object_type_name,),
			lambda type_ID: cmds.BuildCommand(unit_type_ID=type_ID),
		),
}	
	



class Parser (object):
	def __init__(self, input_data, sender_ID):
		self.sender_ID = sender_ID
		self.messages = []
		self.commands = []
		self.invalid_lines_numbers = []
		
		self._parse_input_data(input_data)	
		
	def	_parse_input_data(self, input_data):
		for line_index, line in enumerate(input_data.split('\n')):
			self._line_no = line_index+1
			self._parse_line(line)
			
	def _parse_line(self, line):
		line = line.strip()
		if len(line) == 0:
			return
			
		command, rest_of_line = self._split_to_word_and_rest(line)
		command_as_int = _parse_as_int(command)
		if command_as_int == None:
			self._parse_command(command, rest_of_line)
		else:
			rest_of_line = line[len(command)+1:]
			self._parse_message(command_as_int, rest_of_line)
		
	def _split_to_word_and_rest(self, line):
		splited_line = line.split(None, 1)
		command = splited_line[0]
		rest = splited_line[1] if len(splited_line) >= 2 else ''
		return command, rest

	def _parse_command(self, command_as_string, rest_of_line):
		command_as_string = command_as_string.lower()
		signatures_with_functions_by_number_of_args = commands.get(command_as_string, None)
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
			for i, (function, arg) in enumerate(zip(signature, args_of_command)):
				result = function(arg)
				if result == None:
					self._invalid_line()
					return
				args.append(result)

			command = method(*args)
			self.commands.append(command)	
			
	def _invalid_line(self):
		self.invalid_lines_numbers.append(self._line_no)		
	
	def _parse_message(self, receiver_ID, rest_of_line):
		m = Message(self.sender_ID, receiver_ID, rest_of_line)
		self.messages.append(m)


