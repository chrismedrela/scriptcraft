#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import unittest

from scriptcraft.utils import *
from scriptcraft.core.Game import Game
from scriptcraft.core.GameConfiguration import GameConfiguration
from scriptcraft.core.GameMap import GameMap
from scriptcraft.core.Message import Message
from scriptcraft.core.Program import Program
from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED





class TestGame(unittest.TestCase):

#     Testy TODO
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
#     + store_minerals_from_unit_to_unit(self, source_unit, destination_unit, how_much=None)
#     + store_minerals_from_deposit_to_unit(self, source_position, destination_unit, how_much=None)
#     + new_unit(self, player, position, type)
#       new_player(name, color)
#       new_player_with_startpoint(name, color)
#     + _clear_mailboxes(self)
#     + _send_message(self, message)
#       remove_unit
#       set_program


    def setUp(self):
        unittest.TestCase.setUp(self)

        self._create_unit_types()
        self._create_map_and_game()
        self._create_player_Bob()
        self._modify_world()


    def _create_unit_types(self):
        self.miner_type = UnitType(attack_range=0, vision_range=7,
            store_size=1,
            cost_of_build=3,
            can_build=False,
            movable=True,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
            names=('5', 'miner', 'm'))
        self.base_type = UnitType(attack_range=0,
            vision_range=2,
            store_size= -1,
            cost_of_build= -1,
            can_build=True,
            movable=False,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY,
            names=('4', 'base', 'b'))


    def _create_map_and_game(self):
        self.unit_types = [self.miner_type, self.base_type]
        languages_by_names = {}
        game_configuration = GameConfiguration(units_types=self.unit_types, main_base_type=self.base_type,
            main_miner_type=self.miner_type,
            minerals_for_main_unit_at_start=1,
            probability_of_mineral_deposit_growing=0.1,
            languages_by_names=languages_by_names)
        self.start_positions = [(16, 16), (48, 48), (16, 48), (48, 16)]
        self.map_size = 64, 64
        game_map = GameMap(self.map_size, self.start_positions)
        self.game = Game(game_map, game_configuration)


    def _create_player_Bob(self):
        self.player_Bob = game.new_player_with_startpoint('Bob', (255, 0, 0))
        self.base = self.player_Bob.maybe_base
        self.miners = filter(lambda unit:unit.type == self.miner_type, self.player_Bob.units)
        self.miner = self.miners[0]


    def _modify_world(self):
        self.trees_position = (14, 16)
        self.game.game_map.place_trees_at(self.trees_position)

        self.minerals_position = (26, 27)
        minerals_in_deposit = 20
        self.game.game_map.place_minerals_at(self.minerals_position, minerals_in_deposit)

        self.free_positions = [(35, 36), (35, 37), (35, 38)]
        for free_position in self.free_positions:
            assert self.game.game_map.get_field(free_position).is_empty()


    def test_new_player_with_startpoint(self):
        self.game.new_player_with_startpoint('Alice', (0, 255, 0))

        self.assertEqual(len(game.units_by_IDs), 4 + 1) # 4 miners and 1 base
        self.assertEqual(base.position, self.start_positions[1]) # base
        self.assertTrue(game.game_map[15][16].has_unit()) # here is miner

    def test_new_player(self):
        pass



    def test_generate_input(self):
        message = Message(sender_ID=1234, receiver_ID=self.base.ID, text='\t\ttext of message\t')
        game._send_message(message)
        number_of_messages = 1

        vision_diameter = 2 * self.base.type.vision_range + 1
        base_type_name = self.base_type.main_name

        description_of_field_with_trees = '3 0 0'
        description_of_surroundings = "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      + description_of_field_with_trees + "0 0 0" "%(base_type_name)s %(self.base.ID)d %(self.player.ID)d" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0\n" \
                                      "0 0 0" "0 0 0" "0 0 0" "0 0 0" "0 0 0"
        messages = "%(message.sender_ID) " + message.text
        excepted_input = "%(base_type_name)s %(self.base.ID)d %(self.player.ID)d %(number_of_messages)d %(self.base.position[0])d %(self.base.position[1])d %(vision_diameter)d\n" \
                         "%(self.base.ID)d\n" \
                         "%(description_of_surroundings)s\n" \
                         "%(messages)s" % locals()

        input = game._generate_input_for(self.base)
        self.assertEqual(excepted_input, input)


    @ max_time(50, repeat=3)
    def test_efficiency_of_deepcopy(self):
        copy.deepcopy(self.game)


    def test_searching_nearest_unit(self):
        player_Alice = self.game.new_player('Alice', (255, 0, 0))
        Bob_unit = self.game.new_unit(self.player_Bob, (61, 0), self.miner_type)
        Alice_unit = self.game.new_unit(Alice, (62, 0), self.miner_type)

        position = (65, 0) # out of map
        range = 5
        condition = lambda unit: unit.player.name != 'Alice'

        found_unit = self.game.find_nearest_unit_in_range_fulfilling_condition(position, range, condition)
        excepted_unit = Bob_unit
        self.assertEqual(found_unit, excepted_unit)


    def test_move_unit(self):
        old_position = self.miner.position
        new_position = self.free_positions[0]

        self.game.move_unit_at(self.miner, new_position)

        self.assertTrue(game.game_map.get_field(old_position).is_empty())
        self.assertTrue(game.game_map.get_field(new_position).has_unit())


    def test_cannot_move_unit_on_occuped_field(self):
        old_position = self.miner.position
        new_position = self.base.position

        illegal_operation = lambda: game.move_unit_at(self.miner, new_position)
        self.assertRaises(Exception, illegal_operation)


    def test_fire_trees(self):
        self.game.fire_at(self.trees_position)
        self.game.assertTrue(self.game.game_map.get_field(self.trees_position).is_empty())


    def test_fire_base(self):
        self._test_fire_base_with_minerals()
        self._test_fire_base_without_minerals()


    def _test_fire_base_with_minerals(self):
        assert self.base.minerals == 1
        self.game.fire_at(self.base.position)
        self.game.assertEqual(self.base.minerals, 0)


    def _test_fire_base_without_minerals(self):
        assert self.base.minerals == 0
        self.game.fire_at(self.base.position)
        self.assertTrue(self.base not in self.game.units_by_IDs.itervalues())


    def test_fire_miner(self):
        self.game.fire_at(self.miner.position)
        self.assertTrue(self.miner not in self.game.units_by_IDs.itervalues())


    def test_cannot_fire_out_of_map(self):
        illegal_operation = self.game.fire_at((-1, -1))
        self.assertRaises(Exception, illegal_operation)


    def test_store_minerals(self):
        self._test_store_minerals_from_deposit_to_miner(self.miner)
        self._test_store_minerals_from_miner_to_base(self.miner)


    def _test_store_minerals_from_deposit_to_miner(self, miner):
        minerals_in_deposit = self.game.game_map.get_field(self.minerals_position).get_minerals()

        self.game.store_minerals_from_deposit_to_unit(self.minerals_position, miner)

        self.assertEqual(miner.minerals, 1)
        self.assertEqual(self.game.game_map.get_field(self.minerals_position).get_minerals(), minerals_in_deposit - 1)


    def _test_store_minerals_from_miner_to_base(self, miner):
        minerals_in_base = self.base.minerals

        self.game.store_minerals_from_unit_to_unit(miner, self.base)

        self.assertEqual(miner.minerals, 0)
        self.assertEqual(self.base.minerals, self.minerals_in_base + 1)


    def test_store_minerals_when_destination_is_full(self):
        self.game.store_minerals_from_deposit_to_unit(self.minerals_position, self.miner)
        illegal_operation = lambda: self.game.store_minerals_from_deposit_to_unit(self.minerals_position, self.miner)
        self.assertRaises(Exception, illegal_operation)


    def test_store_minerals_when_mineral_deposit_source_is_empty(self):
        self.game.game_map.place_minerals_at(self.minerals_position, 0)
        illegal_operation = lambda: self.game.store_minerals_from_deposit_to_unit(self.minerals_position, self.miner)
        self.assertRaises(Exception, illegal_operation)


    def test_store_minerals_when_miner_source_is_empty(self):
        illegal_operation = lambda: self.game.store_minerals_from_unit_to_unit(self.miner, self.base)
        self.assertRaises(Exception, illegal_operation)


    def test_new_unit(self):
        miner = game.new_unit(self.player_Bob, self.free_positions[0], self.miner_type)

        self.assertTrue(miner in game.units_by_IDs.itervalues())
        self.assertTrue(miner in player.units)
        self.assertEqual(miner.player, player)


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
        system_message = Message(sender_ID=self.player_Bob.ID, receiver_ID=0,
                                 text=question)

        answer = self.game._generate_answer_to_system_message(system_message)
        excepted_answer = Message(sender_ID=0, receiver_ID=self.player_Bob.ID, text=answer)
        self.assertEqual(excepted_answer, answer)


    def test_send_message(self):
        message = Message(sender_ID=self.base.ID, receiver_ID=self.miner.ID, text='text of message')
        self.game._send_message(message)

        self.assertEqual(self.base.output_messages, [message])
        self.assertEqual(self.miner.input_messages, [message])


    def test_send_system_message(self):
        message = Message(sender_ID=self.base.ID, receiver_ID=0, text='text of message')
        self.game._send_message(message)

        self.assertEqual(self.base.output_messages, [message])
        self.assertEqual(self.game.input_messages, [message])


    def test_send_message_with_invalid_receiver(self):
        message = Message(sender_ID=self.base.ID, receiver_ID=1234567, text='text of message')
        illegal_operation = self.game._send_message(message)

        self.assertRaises(Exception, illegal_operation)


    def test_clear_mailboxes(self):
        message = Message(sender_ID=self.base.ID, receiver_ID=self.miner.ID, text='text of message')
        self.game._send_message(message)
        message = Message(sender_ID=self.base.ID, receiver_ID=0, text='text of message')
        self.game._send_message(message)

        self.game._clear_mailboxes()

        self.assertFalse(self.base.output_messages)
        self.assertFalse(self.miner.input_messages)
        self.assertFalse(self.game.input_messages)

if __name__ == '__main__':
    unittest.main()
