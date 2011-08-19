#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import game

def basic_test():	
	tprogram_code_for_base = """
print '2 bl bl'
print '3 no no'
print '1 a a '
print 'build 6'
	"""
	
	tgame = game.Game(game_map=game.GameMap(size=16, start_positions=[(2,2),(14,2),(2,14)]), players=[])
	tgame.add_player(game.Player(name='Bob'), game.Program(code=tprogram_code_for_base, language_ID=game.PYTHON_LANGUAGE_ID))

	def t():
		tgame.tic()

		print "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nPlayers:"
		for k,v in tgame._players_by_ID.items():
			#print "  player %d -> object_IDs = %s" % (k, v.object_IDs)
			print "%d -> %s" % (k, v)

		print "\n\n\nObjects:"
		for k,v in tgame._objects_by_ID.items():
			print "%d -> %s" % (k, v)
			print "\n".join(map(lambda x: ' '*4+x, v.program_execution.parse_errors.split('\n')))
			print "\n".join(map(lambda x: ' '*4+x, v.program_execution.executing_command_errors.split('\n')))
			print "\n".join(map(lambda x: ' '*4+x, v.program_execution.output.split('\n')))

		#print '\n\n'
		#print tgame._objects_by_ID[1].program_execution.errors_output
		print '\n\n\n\n'
		print tgame._map
		
	while True:
		t()
		i = raw_input()
		if i.lower() == 'e':
			return
			
if __name__ == '__main__':
	basic_test()

