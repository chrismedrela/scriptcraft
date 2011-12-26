#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import unittest

from scriptcraft.utils import *
from scriptcraft.core import actions, cmds
from scriptcraft.core.Game import Game
from scriptcraft.core.GameConfiguration import GameConfiguration
from scriptcraft.core.GameMap import GameMap
from scriptcraft.core.Language import Language
from scriptcraft.core.Message import Message
from scriptcraft.core.Program import Program
from scriptcraft.core.UnitType import UnitType, BEHAVIOUR_WHEN_ATTACKED




class BaseGameTestCase(unittest.TestCase):

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
        self.tank_type = UnitType(attack_range=5, vision_range=7,
            store_size=0,
            cost_of_build=10,
            can_build=False,
            movable=True,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
            names=('6', 'tank', 't'))
        self.unit_types = [self.miner_type, self.base_type, self.tank_type]


    def _create_map_and_game(self):
        self.simple_language = Language(ID='sl', name='simplelang',
                                        source_extension='sl', binary_extension='slbin',
                                        compilation_command='simplelang compile %s',
                                        running_command='simplelang run %s')
        languages_by_names = {'simplelang':self.simple_language}
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
        self.player_Bob = self.game.new_player_with_startpoint('Bob', (255, 0, 0))
        self.base = self.player_Bob.maybe_base
        self.miners = filter(lambda unit:unit.type == self.miner_type, self.player_Bob.units)
        self.miner = self.miners[0]
        self.tank = self.game.new_unit(self.player_Bob, (0,63), self.tank_type)


    def _modify_world(self):
        self.trees_position = (14, 16)
        self.game.game_map.place_trees_at(self.trees_position)

        self.minerals_position = (22, 16)
        self.free_position_nearby_minerals = (21, 16)
        minerals_in_deposit = 20
        self.game.game_map.place_minerals_at(self.minerals_position, minerals_in_deposit)

        self.free_positions = [(35, 36), (35, 37), (35, 38)]
        for free_position in self.free_positions:
            assert self.game.game_map.get_field(free_position).is_empty()



class TestBasic():

    def test_new_player(self):
        color = (255, 0, 0)
        Alice = self.game.new_player('Alice', color)

        self.assertTrue(Alice in self.game.players_by_IDs.itervalues())
        self.assertTrue(Alice.start_position == self.start_positions[1]) # 1st position belongs to Bob


    def test_new_player_with_base(self):
        color = (0, 255, 0)
        Alice, base, miners = self.game.new_player_with_base('Alice', color)

        self.assertEqual(len(Alice.units), 4 + 1) # 4 miners and 1 base
        self.assertEqual(base.position, self.start_positions[1])
        field_with_miner = self.game.game_map[self.start_position[1][0]-1][self.start_position[1][1]]
        self.assertTrue(field_with_miner.has_unit()) # here is miner


    def test_new_unit(self):
        miner = self.game.new_unit(self.player_Bob, self.free_positions[0], self.miner_type)

        self.assertTrue(miner in self.game.units_by_IDs.itervalues())
        self.assertTrue(miner in self.player.units)
        self.assertEqual(miner.player, self.player)


    def test_remove_unit(self):
        self.game.remove_unit(self.base)

        self.assertTrue(self.base.ID not in self.game.units_by_IDs)
        self.assertTrue(self.player.base == None)
        self.assertTrue(self.base not in self.player.units)


    def test_set_program(self):
        program = Program(language=self.simple_language, code='// simple code')
        self.game.set_program(self.base, program)

        self.assertEqual(self.base.program, program)


    def _test_execute_gather_action(self):
        self.miner.action = actions.GatherAction(source=self.mineral_deposit)
        self.game._execute_action_of(self.miner)
        minerals_in_deposit = self.game.game_map.field_at(self.minerals_position).get_minerals()

        self.assertEqual(self.miner.minerals, 1)
        self.assertEqual(self.game.game_map.field_at(self.minerals_position).get_minerals(),
                         minerals_in_deposit - 1)



class TestUtils(BaseGameTestCase):

    def test_searching_nearest_unit(self):
        Alice = self.game.new_player('Alice', (255, 0, 0))
        Bob_unit = self.game.new_unit(self.player_Bob, (61, 0), self.miner_type)
        Alice_unit = self.game.new_unit(Alice, (62, 0), self.miner_type)

        position = (65, 0) # out of map
        range = 5
        condition = lambda unit: unit.player.name != 'Alice'

        found_unit = self.game.find_nearest_unit_in_range_fulfilling_condition(position, range, condition)
        excepted_unit = Bob_unit
        self.assertEqual(found_unit, excepted_unit)


    def test_generate_input(self):
        message = Message(sender_ID=1234, receiver_ID=self.base.ID, text='\t\ttext of message\t')
        self.game._send_message(message)
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

        input = self.game._generate_input_for(self.base)
        self.assertEqual(excepted_input, input)



class TestFire(BaseGameTestCase):

    def test_fire_trees(self):
        self.game.fire_at(self.trees_position)
        self.game.assertTrue(self.game.game_map.get_field(self.trees_position).is_empty())


    def test_fire_miner(self):
        self.game.fire_at(self.miner.position)
        self.assertTrue(self.miner not in self.game.units_by_IDs.itervalues())


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


    def test_cannot_fire_out_of_map(self):
        illegal_operation = self.game.fire_at((-1, -1))
        self.assertRaises(Exception, illegal_operation)



class TestStoreMinerals(BaseGameTestCase):

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
        self.assertEqual(self.base.minerals, minerals_in_base + 1)


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



class TestMoveUnit(BaseGameTestCase):

    def test_move_unit(self):
        old_position = self.miner.position
        new_position = self.free_positions[0]

        self.game.move_unit_at(self.miner, new_position)

        self.assertTrue(self.game.game_map.get_field(old_position).is_empty())
        self.assertTrue(self.game.game_map.get_field(new_position).has_unit())


    def test_cannot_move_unit_on_occuped_field(self):
        new_position_for_miner = self.base.position

        illegal_operation = lambda: self.game.move_unit_at(self.miner, new_position_for_miner)
        self.assertRaises(Exception, illegal_operation)



class TestGenerateActions(BaseGameTestCase):

    def test_generate_action_for_immovable_base_with_complex_move_command(self):
        command = cmds.ComplexMoveCommand(destination=self.free_positions)
        excepted_action = actions.StopAction()
        self._test_generate_action(command, excepted_action, unit=self.base)


    def test_generate_action_for_tank_with_fire_command_when_destination_is_in_attack_range(self):
        destination = (5,63)
        assert distance(destination, self.tank.position) == self.tank.type.attack_range
        self._test_generate_action_for_tank_with_fire_command(destination)


    def test_generate_action_for_tank_with_fire_command_when_destination_is_too_far(self):
        destination = (6,63)
        assert distance(destination, self.tank.position) > self.tank.type.attack_range
        self._test_generate_action_for_tank_with_fire_command(destination)


    def _test_generate_action_for_tank_with_fire_command(self, destination):
        command = cmds.FireCommand(destination)
        excepted_action = actions.StopAction()
        self._test_generate_action(command, excepted_action, unit=self.tank)


    def test_generate_action_for_full_miner_with_complex_gather_command(self):
        self._test_generate_action_for_miner_with_complex_gather_command(minerals_in_miner=self.miner.type.store_size,
                                                                         direction='base')

    def test_generate_action_for_empty_miner_with_complex_gather_command(self):
        self._test_generate_action_for_miner_with_complex_gather_command(minerals_in_miner=0,
                                                                         direction='mineral_deposit')

    def test_generate_action_for_empty_miner_with_complex_gather_command_when_mineral_deposit_is_empty(self):
        self.game.move_unit_at(self.miner, self.free_position_nearby_minerals)
        self.game.game_map.place_minerals_at(self.mineral_position, how_many=0)

        command = cmds.ComplexGatherCommand(self.mineral_position)
        excepted_action = actions.StopAction()
        self._test_generate_action(command, excepted_action, unit=self.miner)


    def _test_generate_action_for_miner_with_complex_gather_command(self, minerals_in_miner, direction):
        assert self.minerals_position == (22, 16)
        assert self.base.position == (16, 16)
        self.game.move_unit_at(self.miner, (19,16))

        destinations = {'base':(18,16),
                        'mineral_deposit':(20,16)}
        destination = destinations[direction]

        self.miner.set_minerals(self.miner.type.store_size)

        command = cmds.ComplexGatherCommand(destination=self.minerals_position)
        excepted_action = actions.MoveAction(source=self.miner.position,
                                             destination=destination)
        self._test_generate_action(command, excepted_action, unit=self.miner)


    def test_generate_action_for_tank_with_complex_attack_command_when_alien_in_destination(self):
        Alice = self.game.new_player('Alice', (0,255,0))
        position = (3, 63)
        alien_unit = self.game.new_unit(Alice, position, self.miner_type)

        assert distance(self.tank.position, alien_unit.position) <= self.tank.type.attack_range

        command = cmds.ComplexAttackCommand(destination=position)
        excepted_action = actions.FireAction(destination=position)
        self._test_generate_action(command, excepted_action, unit=self.tank)


    def test_generate_action_for_tank_with_complex_attack_command_when_an_alien_in_range(self):
        Alice = self.game.new_player('Alice', (0,255,0))
        position = (3, 63)
        alien_unit = self.game.new_unit(Alice, position, self.miner_type)
        destination = (10, 63)

        assert distance(self.tank.position, alien_unit.position) <= self.tank.type.attack_range
        assert distance(self.tank.position, destination) > self.tank.type.attack_range

        command = cmds.ComplexAttackCommand(destination=destination)
        excepted_action = actions.FireAction(destination=position)
        self._test_generate_action(command, excepted_action, unit=self.tank)


    def test_generate_action_for_tank_with_complex_attack_command_when_no_alien_in_range_and_target_not_accured(self):
        assert self.tank.position == (0, 63)
        destination = (2, 63)
        direction = (1, 63)

        command = cmds.ComplexAttackCommand(destination=destination)
        excepted_action=actions.MoveAction(destination=direction)
        self._test_generate_action(command, excepted_action, unit=self.tank)


    def test_generate_action_for_tank_with_complex_attack_command_when_no_alien_in_range_and_target_accured(self):
        assert self.tank.position == (0, 63)
        destination = self.tank.position

        command = cmds.ComplexAttackCommand(destination=destination)
        excepted_action = actions.StopAction()
        self._test_generate_action(command, excepted_action, unit=self.tank)


    def test_generate_action_for_base_with_build_command_when_building_is_possible(self):
        assert self.base.position == (16, 16)
        destination = (15, 16)
        self.game.remove_unit_at(destination)

        command = cmds.BuildCommand(unit_type_name=self.miner_type.main_name)
        excepted_action = actions.BuildAction(unit_type=self.miner_type, destination=destination),
        self._test_generate_action(command, excepted_action, unit=self.base)


    def test_generate_action_for_base_with_build_command_when_all_surrounding_fields_are_occuped(self):
        command = cmds.BuildCommand(unit_type_name=self.miner_type.main_name)
        excepted_action = actions.StopAction()
        self._test_generate_action(command, excepted_action, unit=self.base)


    def _test_generate_action(self, command, excepted_action, unit):
        unit.command = command
        action = self.game._generate_action_for(unit)
        self.assertEqual(action, excepted_action)



class TestMessageSystem(BaseGameTestCase):

    def test_send_message(self):
        """ Sending messages to alien should be legal. """

        _, Alice_base, _ = self.game.new_player_with_base('Alice', (0, 255, 0))
        message = Message(sender_ID=self.base.ID, receiver_ID=Alice_base.ID, text='text of message')
        self.game._send_message(message)

        self.assertEqual(self.base.output_messages, [message])
        self.assertEqual(self.Alice_base.input_messages, [message])


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



class TestAnsweringSystemQuestions(BaseGameTestCase):

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



class TestEfficiency(BaseGameTestCase):

    @ max_time(50, repeat=3)
    def test_efficiency_of_deepcopy(self):
        copy.deepcopy(self.game)



if __name__ == '__main__':
    unittest.main()

