#!/usr/bin/env python
#-*- coding:utf-8 -*-

from collections import namedtuple

from message import Message
import direction
import cmds
import units


# -----------------------------------------------------------------------------
# some usefull functions
# -----------------------------------------------------------------------------

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
		return direction.BY_NAME[data.upper()]
	except KeyError:
		return None

def _parse_as_str(data, max_string_length=256):
	""" W przypadku, gdy długość stringa przekracza max_string_length,
	zwraca None """

	if len(data) > max_string_length:
		return None
	return data

def _split_to_word_and_rest(line):
	splited_line = line.split(None, 1)
	command = splited_line[0]
	rest = splited_line[1] if len(splited_line) >= 2 else ''
	return command, rest



# -----------------------------------------------------------------------------
# globals 
# -----------------------------------------------------------------------------
# _COMMANDS = {
#	<name of command> : {
#		<number of args> : 
#			(	<signature>,
#				<function returning (cmds.*Command)>,
#			) 
#	}
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
			lambda x, y: cmds.ComplexMoveCommand(dest_pos=(x,y)),
		),
}
_COMMANDS['GATHER'] = _COMMANDS['G'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.ComplexGatherCommand(dest_pos=(x,y)),
		),
}
_COMMANDS['FIRE'] = _COMMANDS['F'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.FireCommand(dest_pos=(x,y)),
		),
}
_COMMANDS['ATTACK'] = _COMMANDS['A'] = {
	2 : (
			(_parse_as_int, _parse_as_int),
			lambda x, y: cmds.ComplexAttackCommand(dest_pos=(x,y)),
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
	W konstruktorze podajemy:
	 input_data -- dane do sparsowania (może być wiele wierszy)
	 sender_ID -- będzie używane jako nadawca dla message.Message.
	 
	Dane są parsowane *w konstruktorze* - po utworzeniu parsera mamy już
	sparsowane dane.
	
	Atrybuty dostępne po utworzeniu obiektu:
	 commands : list<cmds.*Command>
	 messages : list<message.Message>
	 invalid_lines_numbers : list<int> -- wiersze są numerowane od jeden
	
	"""

	def __init__(self, input_data, sender_ID):
		self.sender_ID = sender_ID
		self.messages = []
		self.commands = []
		self.invalid_lines_numbers = []
		
		self._parse_input_data(input_data)	
		
	def	_parse_input_data(self, input_data):
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
				m = Message(self.sender_ID, receiver_ID, message_text)
				self.messages.append(m)
			
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


