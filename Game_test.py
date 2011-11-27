#!/usr/bin/env python
#-*- coding:utf-8 -*-

import unittest
import copy

from utils import *

from Game import Game
from GameConfiguration import GameConfiguration
from UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED
from GameMap import GameMap
from Program import Program
from Message import Message



class TestGame(unittest.TestCase):

#     Testy:
#     ------
#     + _generate_input_for
#     + new_player_with_startpoint
#     + deepcopy
#       _generate_action_for(unit)
#       _execute_action_of(unit)
#       _tic_for_world
#       tic()
#     + _generate_answer_to_system_message
#     + _get_the_nearest_unit...
#     + deepcopy
#     + move_unit_at(self, unit, destination)
#     + fire_at(self, destination)
#       store_minerals_from_unit_to_unit(self, source_unit, destination_unit, how_much=None)
#       store_minerals_from_deposit_to_unit(self, source_position, destination_unit, how_much=None)
#       new_unit(self, player, position, type)

    # XXX should move_unit_at and other methods raise exceptions?

    # tests of high-abstract methods
    def test_new_player_with_startpoint(self):
        game = self._generate_simple_game_without_players()
        player = game.new_player_with_startpoint('Bob', (255, 0, 0))
        base = player.maybe_base

        self.assertEqual(len(game.units_by_IDs), 4+1) # 4 miners and 1 base
        self.assertEqual(base.position, (16, 16)) # base
        self.assertTrue(game.game_map[15][16].has_unit()) # here is miner

    # tests of private methods
    def test_generate_input(self):
        game, player = self._generate_simple_game_and_player()
        game.game_map.place_trees_at((14, 16))

        message = Message(sender_ID=1234, receiver_ID=base.ID, text='\t\ttext of message\t')
        game._send_message(message)

        base = player.maybe_base
        vision_diameter = 2*base.type.vision_range+1
        unit_type_name = base.type.names[0]
        number_of_messages = 1

        description_of_field_with_trees = '3 0 0'
        description_of_surroundings = "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      +description_of_field_with_trees+ "0 0 0" "%(unit_type_name)s %(base.ID)d %(player.ID)d" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0"
        messages = "%(message.sender_ID) " + message.text
        excepted_input = "%(unit_type_name)s %(unit.ID)d %(player.ID)d %(number_of_messages)d %(base.position[0])d %(base.position[1])d %(vision_diameter)d\n" \
                         "%(unit.ID)d\n" \
                         "%(description_of_surroundings)s\n" \
                         "%(messages)s" % locals()

        input = game._generate_input_for(base)
        self.assertEqual(excepted_input, input)

    # tests of simple methods
    @ max_time(50, repeat=3)
    def test_efficiency_of_deepcopy(self):
        game = self._generate_simple_game_and_player()
        copy.deepcopy(game)

    def test_searching_nearest_unit(self):
        game = self._generate_simple_game_without_players()
        Bob = game.new_player('Bob', (255, 0, 0))
        Alice = game.new_player('Alice', (255, 0, 0))
        miner_type = game.game_configuration.units_types_by_names['miner']
        Bob_unit = game.new_unit(Bob, (62, 0), miner_type)
        Alice_unit = game.new_unit(Alice, (60, 0), miner_type)

        position = (59, 0)
        range = 5
        condition = lambda unit: unit.player.name != 'Alice'

        unit = game.find_nearest_unit_in_range_fulfilling_condition(position, range, condition)
        excepted_unit = Bob_unit
        self.assertEqual(unit, excepted_unit)

    def test_move_unit(self):
        game, player = self._generate_simple_game_and_player()
        miner = player.units[3]

        old_position = miner.position
        new_position = 45, 44
        game.move_unit_at(miner, new_position)

        self.assertTrue(game.game_map[old_position[0]][old_position[1]].is_empty())
        self.assertTrue(game.game_map[new_position[0]][new_position[1]].has_unit())

    def test_fire(self):
        game, player = self._generate_simple_game_and_player()

        # fire trees
        game.game_map.place_trees_at((30, 30))
        game.fire_at((30, 30))
        game.assertTrue(game.game_map[30][30].is_empty())

        # fire base with minerals
        base = player.maybe_base
        assert base.minerals==1
        game.fire_at(base.position)
        game.assertEqual(base.minerals, 0)

        # fire base without minerals
        game.fire_at(base.position)
        field_with_base = game.game_map[base.position[0]][base.position[1]]
        game.assertFalse(field_with_base.has_unit())
        game.assertEqual(player.maybe_base, None)

        # fire miner
        miner = game.units_by_IDs[3]
        assert miner.type == game.game_configuration.unit_types_by_names['miner']
        game.fire_at(miner.position)
        field_with_miner = game.game_map[miner.position[0]][miner.position[1]]
        game.assertTrue(field_with_miner.is_empty())
        game.assertTrue(miner not in Bob.units)

    # message system tests
    def test_answering_system_question_about_list_of_units(self):
        full_question = ' lISt\tunItS '
        short_question = ' lU\t'
        answer = '5' '2 4' '3 5' '4 5' '5 5' '6 5'
        self._test_correctness_of_answer_to_system_question(full_question, answer)
        self._test_correctness_of_answer_to_system_question(short_question, answer)

    def test_answering_system_question_about_unit(self):
        full_question = ' uNit \t1 '
        short_question = 'u 1'
        answer = '1 4 16 16 10'
        self._test_correctness_of_answer_to_system_question(full_question, answer)
        self._test_correctness_of_answer_to_system_question(short_question, answer)

    def _test_correctness_of_answer_to_system_question(self, question, answer):
        game, player = self._generate_simple_game_and_player()
        system_message = Message(sender_ID=1, receiver_ID=0, text=question)

        answer = game._generate_answer_to_system_message(system_message)
        excepted_answer = Message(sender_ID=0, receiver_ID=1, text=answer)
        self.assertEqual(excepted_answer, answer)


    # helpful methods
    def _generate_simple_game_and_player(self):
        game = self._generate_simple_game_without_players()
        player = game.new_player_with_startpoint('Bob', (255, 0, 0))
        return game, player

    def _generate_simple_game_without_players(self):
        base_type = self._generate_base_type()
        miner_type = self._generate_miner_type()
        unit_types = [base_type, miner_type]

        game_configuration = GameConfiguration(units_types_by_names=unit_types,
                                               main_base_type=base_type,
                                               main_miner_type=miner_type,
                                               minerals_for_main_unit_at_start=1,
                                               probability_of_mineral_deposit_growing=0.1,
                                               languages_by_names=languages_by_names)

        start_positions = [(16, 16), (48, 48), (16, 48), (48, 16)]
        game_map = GameMap((64, 64), start_positions)
        game = Game(game_map, game_configuration)
        return game

    def _generate_miner_type(self):
        return UnitType(attack_range=0,
                        vision_range=7,
                        store_size=1,
                        cost_of_build=3,
                        can_build=False,
                        movable=True,
                        behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                        names=('5', 'miner', 'm'))

    def _generate_base_type(self):
        return UnitType(attack_range=0,
                        vision_range=2,
                        store_size=-1,
                        cost_of_build=-1,
                        can_build=True,
                        movable=False,
                        behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY,
                        names=('4', 'base', 'b'))

if __name__ == '__main__':
    unittest.main()