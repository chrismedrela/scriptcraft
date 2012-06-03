#!/usr/bin/env python
#-*- coding:utf-8 -*-

import copy
import os
import unittest
import shutil

from scriptcraft import direction
from scriptcraft.compilation import CompileAndRunProgram
from scriptcraft.gamemap import GameMap, FieldIsOccupied
from scriptcraft.gamestate import *
from scriptcraft.utils import *



class BaseGameTestCase(unittest.TestCase):
    def _prepare_game(self, many_starting_points=False):
        self._create_unit_types()
        self._create_map_and_game(many_starting_points)
        self._create_player_Bob()
        self._modify_world()

    def _create_unit_types(self):
        self.miner_type = UnitType(
            attack_range=0,
            vision_radius=7,
            storage_size=1,
            build_cost=3,
            can_build=False,
            movable=True,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
            names=('5', 'miner', 'm')
        )

        self.base_type = UnitType(
            attack_range=0,
            vision_radius=2,
            has_storage=True,
            storage_size= -1,
            can_be_built=False,
            can_build=True,
            movable=False,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY,
            names=('4', 'base', 'b')
        )

        self.tank_type = UnitType(
            can_attack=True,
            attack_range=5,
            vision_radius=2,
            has_storage=False,
            build_cost=10,
            can_build=False,
            movable=True,
            behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
            names=('6', 'tank', 't')
        )

        self.unit_types = [self.miner_type, self.base_type, self.tank_type]

    def _create_map_and_game(self, many_starting_points):
        game_configuration = GameConfiguration(
            units_types=self.unit_types,
            main_base_type=self.base_type,
            main_miner_type=self.miner_type,
            minerals_for_main_unit_at_start=1,
            probability_of_mineral_deposit_growing=1.0,
        )

        if many_starting_points:
            self.start_positions = [(16, 16), (48, 48), (16, 48), (48, 16)]
        else:
            self.start_positions = [(16, 16)]
        self.map_size = (64, 64)
        game_map = GameMap(self.map_size, self.start_positions)
        self.game = Game(game_map, game_configuration)

    def _create_player_Bob(self):
        self.player, self.base, self.miners = \
            self.game.new_player_with_units('Bob', (255, 0, 0))
        self.miner = self.miners[0]
        self.tank = self.game.new_unit(self.player, (0,63), self.tank_type)

    def _modify_world(self):
        self.trees_position = (2, 62)
        self.game.game_map[self.trees_position].place_object(Tree())

        self.minerals_position = (22, 16)
        self.free_position_nearby_minerals = (21, 16)
        minerals_in_deposit = 20
        mineral_deposit = MineralDeposit(minerals_in_deposit)
        self.game.game_map[self.minerals_position].place_object(mineral_deposit)

        self.free_positions = [(35, 36), (35, 37), (35, 38)]
        assert all(self.game.game_map[free_position].empty
                   for free_position in self.free_positions)



class TestBasic(BaseGameTestCase):
    def test_new_player(self):
        self._prepare_game(many_starting_points=True)

        color = (255, 0, 0)
        Alice = self.game.new_player('Alice', color)

        self.assertTrue(Alice in self.game.players_by_IDs.itervalues())
        self.assertTrue(Alice.start_position in self.start_positions)
        self.assertTrue(Alice.start_position != self.player.start_position)

    def test_new_player_with_base(self):
        self._prepare_game(many_starting_points=True)

        color = (0, 255, 0)
        Alice, base, miners = self.game.new_player_with_units('Alice', color)

        self.assertEqual(len(Alice.units), 4 + 1) # 4 miners and 1 base
        self.assertTrue(base.position in self.start_positions)
        self.assertTrue(Alice.maybe_base != None)
        for miner in miners:
            field_with_miner = self.game.game_map[miner.position]
            self.assertTrue(field_with_miner.maybe_object)
            self.assertTrue(distance(miner.position, base.position) == 1)

    def test_new_unit(self):
        self._prepare_game()

        miner = self.game.new_unit(self.player, self.free_positions[0],
                                   self.miner_type)

        self.assertTrue(miner in self.game.units_by_IDs.itervalues())
        self.assertTrue(miner in self.player.units)
        self.assertEqual(miner.player, self.player)

    def test_new_unit_on_occupied_field(self):
        self._prepare_game()
        illegal_operation = lambda: self.game.new_unit(self.player,
                                                       self.base.position,
                                                       self.miner_type)
        self.assertRaises(FieldIsOccupied, illegal_operation)

    def test_remove_unit(self):
        self._prepare_game()

        self.game.remove_unit(self.base)

        self.assertTrue(self.base.ID not in self.game.units_by_IDs)
        self.assertTrue(self.player.maybe_base == None)
        self.assertTrue(self.base not in self.player.units)

    def test_set_program(self):
        self._prepare_game()

        program = Program(Language.PYTHON, code='# simple code')
        self.game.set_program(self.base, program)

        self.assertEqual(self.base.program, program)


class TestUtils(BaseGameTestCase):
    def test_searching_nearest_unit(self):
        self._prepare_game(many_starting_points=True)
        Alice = self.game.new_player('Alice', (255, 0, 0))
        Bob_unit = self.game.new_unit(self.player, (61, 0), self.miner_type)
        Alice_unit = self.game.new_unit(Alice, (62, 0), self.miner_type)

        found_unit = self.game.find_nearest_unit_in_range_fulfilling_condition(
            center=(65, 0),
            range=5,
            condition=lambda unit: unit != Alice_unit)
        expected_unit = Bob_unit
        self.assertEqual(found_unit, expected_unit)

    def test_generate_input(self):
        self._prepare_game()
        assert self.trees_position == (2, 62)
        assert self.tank.type.vision_radius == 2

        message = Message(sender_ID=self.miner.ID,
                          receiver_ID=self.tank.ID,
                          text='\t\ttext of message\t')
        self.game._send_message(message)
        number_of_messages = 1

        surroundings_dict = {'tank_type_name':self.tank.type.main_name,
                             'tank_ID':self.tank.ID,
                             'player_ID':self.player.ID}
        field_with_trees = '3 0 0'
        surroundings = ("1 0 0 " "1 0 0 " "0 0 0 " "0 0 0 " "0 0 0\n" \
                        "1 0 0 " "1 0 0 " "0 0 0 " "0 0 0 " +field_with_trees+ "\n" \
                        "1 0 0 " "1 0 0 " "%(tank_type_name)s %(tank_ID)d %(player_ID)d " "0 0 0 " "0 0 0\n" \
                        "1 0 0 " "1 0 0 " "1 0 0 " "1 0 0 " "1 0 0\n" \
                        "1 0 0 " "1 0 0 " "1 0 0 " "1 0 0 " "1 0 0") % surroundings_dict

        messages = "%(sender_ID)d " % {'sender_ID':message.sender_ID} \
            + message.text
        expected_input_dict = {'tank_type_name':self.tank.type.main_name,
                               'tank_ID':self.tank.ID,
                               'player_ID':self.player.ID,
                               'messages_len':number_of_messages,
                               'tank_x':self.tank.position[0],
                               'tank_y':self.tank.position[1],
                               'vision_diameter':2 * self.tank.type.vision_radius + 1,
                               'range_of_attack':self.tank.type.attack_range,
                               'messages':messages,
                               'surroundings':surroundings}
        expected_input = "%(tank_type_name)s %(tank_ID)d %(player_ID)d %(messages_len)d %(tank_x)d %(tank_y)d %(vision_diameter)d\n" \
                         "%(range_of_attack)d\n" \
                         "%(surroundings)s\n" \
                         "%(messages)s" % expected_input_dict

        input = self.game._generate_input_for(self.tank)
        self.assertEqual(expected_input, input)


class TestFire(BaseGameTestCase):
    def setUp(self):
        super(TestFire, self).setUp()
        self._prepare_game()

    def test_fire_trees(self):
        self.game.fire_at(self.trees_position)
        self.assertTrue(self.game.game_map[self.trees_position].empty)

    def test_fire_miner(self):
        self.game.fire_at(self.miner.position)
        self.assertTrue(self.miner not in self.game.units_by_IDs.itervalues())

    def test_fire_base(self):
        self._test_fire_base_with_minerals()
        self._test_fire_base_without_minerals()

    def _test_fire_base_with_minerals(self):
        assert self.base.minerals == 1
        self.game.fire_at(self.base.position)
        self.assertEqual(self.base.minerals, 0)

    def _test_fire_base_without_minerals(self):
        assert self.base.minerals == 0
        self.game.fire_at(self.base.position)
        self.assertTrue(self.base not in self.game.units_by_IDs.itervalues())

    def test_cannot_fire_out_of_map(self):
        illegal_operation = lambda: self.game.fire_at((-1, -1))
        self.assertRaises(AssertionError, illegal_operation)


class TestStoreMinerals(BaseGameTestCase):
    def setUp(self):
        super(TestStoreMinerals, self).setUp()
        self._prepare_game()

    def test_store_minerals(self):
        self._test_store_minerals_from_deposit_to_miner(self.miner)
        self._test_store_minerals_from_miner_to_base(self.miner)

    def _test_store_minerals_from_deposit_to_miner(self, miner):
        minerals_in_deposit = \
          self.game.game_map[self.minerals_position].maybe_object.minerals
        self.game.store_minerals_from_deposit_to_unit( \
          self.minerals_position, miner)

        self.assertEqual(miner.minerals, 1)
        self.assertEqual(minerals_in_deposit - 1, \
          self.game.game_map[self.minerals_position].maybe_object.minerals)

    def _test_store_minerals_from_miner_to_base(self, miner):
        minerals_in_base = self.base.minerals

        self.game.store_minerals_from_unit_to_unit(miner, self.base)

        self.assertEqual(miner.minerals, 0)
        self.assertEqual(self.base.minerals, minerals_in_base + 1)

    def test_store_minerals_when_destination_is_full(self):
        self.game.store_minerals_from_deposit_to_unit( \
          self.minerals_position, self.miner)
        illegal_operation = lambda: \
          self.game.store_minerals_from_deposit_to_unit( \
          self.minerals_position, self.miner)
        self.assertRaises(CannotStoreMinerals, illegal_operation)

    def test_store_minerals_when_mineral_deposit_source_is_empty(self):
        self.game.game_map[self.minerals_position].place_object(None)
        mineral_deposit = MineralDeposit(0)
        self.game.game_map[self.minerals_position].place_object(mineral_deposit)
        illegal_operation = lambda: \
          self.game.store_minerals_from_deposit_to_unit( \
          self.minerals_position, self.miner)
        self.assertRaises(CannotStoreMinerals, illegal_operation)

    def test_store_minerals_when_miner_source_is_empty(self):
        illegal_operation = lambda: \
          self.game.store_minerals_from_unit_to_unit(self.miner, self.base)
        self.assertRaises(CannotStoreMinerals, illegal_operation)


class TestMoveUnit(BaseGameTestCase):
    def setUp(self):
        super(TestMoveUnit, self).setUp()
        self._prepare_game()

    def test_move_unit(self):
        old_position = self.miner.position
        new_position = self.free_positions[0]

        self.game.move_unit_at(self.miner, new_position)

        self.assertTrue(self.game.game_map[old_position].empty)
        self.assertTrue(self.game.game_map[new_position].maybe_object)

    def test_cannot_move_unit_on_occuped_field(self):
        illegal_operation = lambda: \
          self.game.move_unit_at(self.miner, self.base.position)
        self.assertRaises(FieldIsOccupied, illegal_operation)


class BaseGenerateActionTestCase(BaseGameTestCase):
    def _assert_stop_action_for_command(self, command, unit):
        expected_action = actions.StopAction()
        self._test_generate_action(command, expected_action, unit)

    def _test_generate_action(self, command, expected_action, unit):
        unit.command = command
        action = self.game._generate_action_for(unit)
        self.assertEqual(action, expected_action)


class TestGenerateActionsForMoveCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForMoveCommand, self).setUp()
        self._prepare_game()

    def test_miner(self):
        old_position = self.tank.position
        new_position = old_position[0], old_position[1] - 1
        command = cmds.MoveCommand(direction=direction.N)
        expected_action = actions.MoveAction(source=old_position,
                                             destination=new_position)
        self._test_generate_action(command, expected_action, unit=self.tank)

    def test_miner_on_border(self):
        self.game.move_unit_at(self.miner, (2, 0))

        invalid_command = cmds.MoveCommand(direction=direction.N)
        self._assert_stop_action_for_command(invalid_command,
                                             unit=self.miner)

    def test_destination_occupied(self):
        assert self.miner.position == (16, 17)
        assert self.base.position == (16, 16)
        command = cmds.MoveCommand(direction.N)
        self._assert_stop_action_for_command(command, unit=self.miner)

    def test_immovable_base(self):
        command = cmds.MoveCommand(direction.N)
        self._assert_stop_action_for_command(command, unit=self.base)


class TestGenerateActionsForFireCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForFireCommand, self).setUp()
        self._prepare_game()

    def test_destination_in_attack_range(self):
        destination = (5,63)
        assert (distance(destination, self.tank.position) == \
                self.tank.type.attack_range)
        expected_action = actions.FireAction(destination)
        self._test_tank(destination, expected_action)

    def test_destination_too_far(self):
        destination = (6,63)
        assert (distance(destination, self.tank.position) > \
                self.tank.type.attack_range)
        expected_action = actions.StopAction()
        self._test_tank(destination, expected_action)

    def _test_tank(self, destination, expected_action):
        command = cmds.FireCommand(destination)
        self._test_generate_action(command, expected_action, unit=self.tank)

    def test_base_that_cannot_attack(self):
        command = cmds.FireCommand(self.miner.position)
        self._assert_stop_action_for_command(command, unit=self.base)

    def test_cannot_fire_self(self):
        command = cmds.FireCommand(self.tank.position)
        self._assert_stop_action_for_command(command, unit=self.tank)

    def test_invalid_destination(self):
        command = cmds.FireCommand((10000, 0))
        self._assert_stop_action_for_command(command, unit=self.tank)


class TestGenerateActionsForBuildCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForBuildCommand, self).setUp()
        self._prepare_game()

    def test_basic(self):
        assert self.base.position == (16, 16)
        self.base.minerals = 100

        destination = (15, 16)

        unit = self.game.game_map[destination].maybe_object
        self.game.remove_unit(unit)

        command = cmds.BuildCommand(unit_type_name=self.miner_type.main_name)
        expected_action = actions.BuildAction(self.miner_type, destination)
        self._test_generate_action(command, expected_action, unit=self.base)

    def test_all_neighbours_occupied(self):
        self.base.minerals = 100
        command = cmds.BuildCommand(unit_type_name=self.miner_type.main_name)
        self._assert_stop_action_for_command(command, unit=self.base)

    def test_unit_not_buildable(self):
        self.game.remove_unit(self.miner)
        command = cmds.BuildCommand(unit_type_name=self.base.type.main_name)
        self._assert_stop_action_for_command(command, unit=self.base)

    def test_invalid_unit_type_name(self):
        self.game.remove_unit(self.miner)
        command = cmds.BuildCommand(unit_type_name='invalid type name')
        self._assert_stop_action_for_command(command, unit=self.base)

    def test_miner_that_cannot_build(self):
        command = cmds.BuildCommand(unit_type_name=self.miner_type.main_name)
        self._assert_stop_action_for_command(command, unit=self.miner)


class TestGenerateActionsForComplexMoveCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForComplexMoveCommand, self).setUp()
        self._prepare_game()

    def test_invalid_destination(self):
        invalid_command = cmds.ComplexMoveCommand(destination=(10000, 0))
        self._assert_stop_action_for_command(invalid_command, unit=self.miner)

    def test_immovable_base(self):
        command = cmds.ComplexMoveCommand(destination=self.free_positions)
        self._assert_stop_action_for_command(command, unit=self.base)


class TestGenerateActionsForComplexGatherCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForComplexGatherCommand, self).setUp()
        self._prepare_game()

    def test_full_miner(self):
        self._test_miner(minerals_in_miner=self.miner.type.storage_size,
                         direction='base')

    def test_empty_miner(self):
        self._test_miner(minerals_in_miner=0,
                         direction='mineral_deposit')

    def _test_miner(self, minerals_in_miner, direction):
        assert self.minerals_position == (22, 16)
        assert self.base.position == (16, 16)

        self.game.move_unit_at(self.miner, (19,16))

        unit_to_remove = self.game.game_map[17, 16].maybe_object
        self.game.remove_unit(unit_to_remove)

        destinations = {'base':(18,16),
                        'mineral_deposit':(20,16)}
        destination = destinations[direction]

        self.miner.minerals = minerals_in_miner

        command = cmds.ComplexGatherCommand( \
          destination=self.minerals_position)
        expected_action = actions.MoveAction(source=self.miner.position,
                                             destination=destination)
        self._test_generate_action(command, expected_action, unit=self.miner)

    def test_empty_miner_nearby_mineral_deposit(self):
        self.game.move_unit_at(self.miner,
                               self.free_position_nearby_minerals)
        command = cmds.ComplexGatherCommand(self.minerals_position)
        expected_action = actions.GatherAction(source=self.minerals_position)
        self._test_generate_action(command, expected_action, unit=self.miner)

    def test_empty_miner_and_empty_mineral_deposit(self):
        self.game.move_unit_at(self.miner, self.free_position_nearby_minerals)
        self.game.game_map[self.minerals_position].place_object(None)
        mineral_deposit = MineralDeposit(0)
        self.game.game_map[self.minerals_position].place_object(mineral_deposit)

        command = cmds.ComplexGatherCommand(self.minerals_position)
        self._assert_stop_action_for_command(command, unit=self.miner)

    def test_tank_without_storage(self):
        command = cmds.ComplexGatherCommand(self.minerals_position)
        self._assert_stop_action_for_command(command, unit=self.tank)

    def test_position_out_of_map(self):
        command = cmds.ComplexGatherCommand((10000, 0))
        self._assert_stop_action_for_command(command, unit=self.miner)

    def test_position_without_mineral_deposit(self):
        command = cmds.ComplexGatherCommand(self.free_positions[0])
        self._assert_stop_action_for_command(command, unit=self.miner)

    def test_full_miner_no_base(self):
        self.miner.minerals = self.miner.type.storage_size
        self.game.remove_unit(self.base)
        command = cmds.ComplexGatherCommand(self.minerals_position)
        self._assert_stop_action_for_command(command, unit=self.miner)


class TestGenerateActionsForComplexAttackCommand(BaseGenerateActionTestCase):
    def setUp(self):
        super(TestGenerateActionsForComplexAttackCommand, self).setUp()
        self._prepare_game(many_starting_points=True)

    def test_alien_in_destination(self):
        destination_of_attack = position_of_alien = (3, 63)
        self._test_tank(position_of_alien, destination_of_attack)

    def test_alien_in_range(self):
        position_of_alien = (3, 63)
        destination = (10, 63)
        self._test_tank(position_of_alien, destination)

    def _test_tank(self, position, destination):
        Alice = self.game.new_player('Alice', (0,255,0))
        alien_unit = self.game.new_unit(Alice, position, self.miner_type)

        assert self.tank.position == (0,63)
        assert (distance(self.tank.position, alien_unit.position) <= \
                self.tank.type.attack_range)

        command = cmds.ComplexAttackCommand(destination)
        expected_action = actions.FireAction(position)
        self._test_generate_action(command, expected_action, unit=self.tank)

    def test_no_alien_and_target_accessible(self):
        assert self.tank.position == (0, 63)
        destination = (2, 63)
        direction = (1, 63)

        command = cmds.ComplexAttackCommand(destination)
        expected_action=actions.MoveAction(source=self.tank.position,
                                           destination=direction)
        self._test_generate_action(command, expected_action, unit=self.tank)

    def test_no_alien_and_target_occupied(self):
        assert self.tank.position == (0, 63)
        destination = self.tank.position

        command = cmds.ComplexAttackCommand(destination)
        self._assert_stop_action_for_command(command, unit=self.tank)

    def test_miner_that_cannot_attack(self):
        command = cmds.ComplexAttackCommand(self.base.position)
        self._assert_stop_action_for_command(command, unit=self.miner)

    def test_invalid_position(self):
        command = cmds.ComplexAttackCommand((10000, 0))
        self._assert_stop_action_for_command(command, unit=self.tank)

    def test_cannot_attack_self(self):
        command = cmds.ComplexAttackCommand(self.tank.position)
        self._assert_stop_action_for_command(command, unit=self.tank)


class TestExecuteActions(BaseGameTestCase):
    def test_gather_action(self):
        self._prepare_game()
        minerals_in_deposit = \
          self.game.game_map[self.minerals_position].maybe_object.minerals
        self.miner.action = actions.GatherAction( \
          source=self.minerals_position)

        self.game._execute_action_for(self.miner)

        self.assertEqual(self.miner.minerals, 1)
        self.assertEqual(minerals_in_deposit - 1, \
          self.game.game_map[self.minerals_position].maybe_object.minerals)


class TestMessageSystem(BaseGameTestCase):
    def test_send_message_between_players_allowed(self):
        self._prepare_game(many_starting_points=True)
        _, Alice_base, _ = self.game.new_player_with_units('Alice', (0, 255, 0))
        message = Message(sender_ID=self.base.ID,
                          receiver_ID=Alice_base.ID,
                          text='text of message')
        self.game._send_message(message)

        self.assertEqual(self.base.outbox, [message])
        self.assertEqual(Alice_base.inbox, [message])

    def test_send_system_message(self):
        self._prepare_game()
        message = Message(sender_ID=self.base.ID,
                          receiver_ID=0,
                          text='text of message')
        self.game._send_message(message)

        self.assertEqual(self.base.outbox, [message])
        self.assertEqual(self.game.inbox, [message])

    def test_send_message_with_invalid_receiver(self):
        self._prepare_game()
        message = Message(sender_ID=self.base.ID,
                          receiver_ID=1234567,
                          text='text of message')
        assert 1234567 not in self.game.units_by_IDs
        illegal_operation = lambda: self.game._send_message(message)

        self.assertRaises(InvalidReceiver, illegal_operation)

    def test_send_message_with_invalid_sender(self):
        self._prepare_game()
        message = Message(sender_ID=1234567,
                          receiver_ID=self.base.ID,
                          text='text of message')
        assert 1234567 not in self.game.units_by_IDs
        illegal_operation = lambda: self.game._send_message(message)

        self.assertRaises(InvalidSender, illegal_operation)

    def test_clear_mailboxes(self):
        self._prepare_game()
        message = Message(sender_ID=self.base.ID,
                          receiver_ID=self.miner.ID,
                          text='text of message')
        self.game._send_message(message)

        message = Message(sender_ID=self.base.ID,
                          receiver_ID=0,
                          text='text of message')
        self.game._send_message(message)

        self.game._clear_mailboxes()

        self.assertFalse(self.base.outbox)
        self.assertFalse(self.miner.inbox)
        self.assertFalse(self.game.inbox)


class TestAnsweringSystemRequest(BaseGameTestCase):
    def setUp(self):
        super(TestAnsweringSystemRequest, self).setUp()
        self._prepare_game()

    def test_list_of_units_request(self):
        assert len(self.player.units) == 6

        full_question = ' lISt\tunItS '
        short_question = ' lU\t'
        answer = '6 ' '2 4 ' '3 5 ' '4 5 ' '5 5 ' '6 5 ' '7 6'

        self._test_requests_correctness_demanded_by_base(full_question, answer)
        self._test_requests_correctness_demanded_by_base(short_question, answer)

    def test_unit_info_request(self):
        assert self.base.ID == 2

        full_question = ' uNit \t2 '
        short_question = 'u 2'
        answer = '2 4 16 16 1' # ID, type, x, y, minerals or attack_range

        self._test_requests_correctness_demanded_by_base(full_question, answer)
        self._test_requests_correctness_demanded_by_base(short_question, answer)

    def test_invalid_request(self):
        question = 'invalid question'

        system_message = self._generate_system_request_demanded_by_base(question)
        answer = self.game._generate_answer_to_system_message(system_message)
        expected_answer = None
        self.assertEqual(expected_answer, answer)

    def test_request_not_existing_unit(self):
        question = 'unit 12345'
        assert 12345 not in self.game.units_by_IDs

        system_message = self._generate_system_request_demanded_by_base(question)
        self._assert_no_reply_to(system_message)

    def test_invalid_unit_info_request_with_non_numerical_ID(self):
        question = 'unit blabla'

        system_message = self._generate_system_request_demanded_by_base(question)
        self._assert_no_reply_to(system_message)

    def _test_requests_correctness_demanded_by_base(self, question, answer):
        system_message = self._generate_system_request_demanded_by_base(question)

        answer_message = self.game._generate_answer_to_system_message(system_message)
        expected_answer_message = Message(sender_ID=0,
                                          receiver_ID=self.base.ID,
                                          text=answer)
        self.assertEqual(expected_answer_message, answer_message)

    def _generate_system_request_demanded_by_base(self, question):
        return Message(sender_ID=self.base.ID,
                       receiver_ID=0,
                       text=question)

    def _assert_no_reply_to(self, message):
        reply = self.game._generate_answer_to_system_message(message)
        self.assertEqual(reply, None)


class TestGameEfficiency(BaseGameTestCase):
    def setUp(self):
        super(TestGameEfficiency, self).setUp()
        self._prepare_game()

    @ max_time(50, repeat=3)
    def test_efficiency_of_deepcopy(self):
        game_copy = copy.deepcopy(self.game)


class TestGameTic(BaseGameTestCase):
    def setUp(self):
        super(TestGameTic, self).setUp()
        self._prepare_game()
        self.directory = 'tmp_unittest'
        self.file_system = TemporaryFileSystem(self.directory)
        self._create_compile_and_run_function()

    def _create_compile_and_run_function(self):
        self.compile_and_run = CompileAndRunProgram(
            self.directory,
            {Language.PYTHON:'src.py'},
            {Language.PYTHON:'bin.py'},
            {Language.PYTHON:'cp src.py bin.py'},
            {Language.PYTHON:'python bin.py'}
        )

    def test_tic(self):
        try:
            assert self.tank.position == (0, 63)

            code_source_for_base = """
print "BUILD TANK"
print "3 message"
print "1234567 message with invalid receiver"
print "0 list units"
print "%d MOVE 5 63" # command for tank
            """ % self.tank.ID

            code_source_for_miner = """
print "MOVE 15 15"
            """

            program_for_base = Program(Language.PYTHON,
                                       code_source_for_base)
            program_for_miner = Program(Language.PYTHON,
                                        code_source_for_miner)
            program_for_tank = STAR_PROGRAM
            self.game.set_program(self.base, program_for_base)
            self.game.set_program(self.miner, program_for_miner)
            self.game.set_program(self.tank, program_for_tank)

            self.game.tic(self.compile_and_run)
            self.game.tic(self.compile_and_run)

            self.assertTrue(self.base.maybe_run_status != None)
            self.assertTrue(self.miner.maybe_run_status != None)
            self.assertTrue(self.tank.maybe_run_status != None)
            self.assertEqual(self.tank.position, (1, 63))

        finally:
            self.file_system.delete_files_and_folders()

    def test_tic_for_world(self):
        assert self.game.configuration.probability_of_mineral_deposit_growing == 1.0
        old_minerals_amount = \
          self.game.game_map[self.minerals_position].maybe_object.minerals

        self.game._tic_for_world()

        new_minerals_amount = \
          self.game.game_map[self.minerals_position].maybe_object.minerals
        self.assertEqual(new_minerals_amount, old_minerals_amount+1)


class TestGameConfiguration(unittest.TestCase):
    def setUp(self):
        self._create_unit_types()

        self.kwargs = {'units_types':self.unit_types,
                       'main_base_type':self.miner_type,
                       'main_miner_type':self.miner_type,
                       'minerals_for_main_unit_at_start':10,
                       'probability_of_mineral_deposit_growing':0.1}

    def _create_unit_types(self):
        kwargs = {'attack_range':0,
                  'vision_radius':7,
                  'storage_size':1,
                  'build_cost':3,
                  'can_build':False,
                  'movable':True,
                  'behaviour_when_attacked':BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                  'names':('5', 'miner', 'm')}
        self.miner_type = UnitType(**kwargs)

        kwargs['names'] = ('7', 'superminer', 'm')
        self.second_miner_type = UnitType(**kwargs)

        self.unit_types = [self.miner_type]

    def test_unit_types_must_have_unique_names(self):
        self.kwargs['units_types'] = [self.miner_type,
                                      self.second_miner_type]

        self._test_game_configuration_cannot_be_created()

    def test_main_base_type_must_be_in_units_types(self):
        self.kwargs['units_types'] = [self.second_miner_type]
        self.kwargs['main_base_type'] = self.miner_type

        self._test_game_configuration_cannot_be_created()

    def test_deep_copy(self):
        configuration = GameConfiguration(**self.kwargs)
        configuration_copy = copy.deepcopy(configuration)
        self.assertEqual(configuration, configuration_copy)

    def _test_game_configuration_cannot_be_created(self):
        illegal_operation = lambda: GameConfiguration(**self.kwargs)
        self.assertRaises(ValueError, illegal_operation)


class TestPlayer(unittest.TestCase):
    def test_add_base_and_remove_it(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit(player)

        player.add_unit(unit)
        player.set_base(unit)
        self.assertEqual(unit.player, player)
        self.assertEqual(player.units, [unit])
        self.assertEqual(player.maybe_base, unit)

        player.remove_unit(unit)
        self.assertEqual(player.units, [])
        self.assertEqual(player.maybe_base, None)
        self.assertEqual(unit.player, None)

    def test_to_str(self):
        player = self._build_simple_player()
        unit = self._build_simple_unit(player)
        player.add_unit(unit)

        expected = ("<Player:14 | color (255, 0, 0) started at (3, 4) "
                    "with units {7}")
        self.assertEqual(expected, str(player))

    def _build_simple_player(self):
        color = (255, 0, 0)
        ID = 14
        start_position = (3, 4)
        result = Player("name", color, ID, start_position)
        return result

    def _build_simple_unit(self, player):
        unit_type = UnitType(attack_range=5,
                             vision_radius=10,
                             storage_size=0,
                             build_cost=5,
                             can_build=False,
                             movable=True,
                             behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                             names=['tank', 't'])
        unit = Unit(player=player, type=unit_type, position=(2, 3), ID=7)
        return unit



class TestUnit(unittest.TestCase):
    def test_to_str(self):
        unit_type = self._build_simple_unit_type()
        player = self._build_simple_player()
        unit = Unit(player=player, type=unit_type, position=(2, 3), ID=7)
        unit.program = STAR_PROGRAM

        expected = ("<Unit:7 | tank of player 14 at (2, 3) "
                    "with star program with <Command stop> "
                    "doing <Action stop>>")
        self.assertEqual(str(unit), expected)

    def _build_simple_unit_type(self):
        return UnitType(attack_range=5,
                        vision_radius=10,
                        storage_size=0,
                        build_cost=5,
                        can_build=False,
                        movable=True,
                        behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                        names=['tank', 't'])

    def _build_simple_player(self):
        color = (255, 0, 0)
        ID = 14
        start_position = (3, 4)
        result = Player("name", color, ID, start_position)
        return result


class TestRunStarProgram(unittest.TestCase):
    def test_basic(self):
        input = """4 2 1 3 7 7 1
                   10
                   4 2 1
                   3 message
                   423\t message message
                   12"""
        excepted_output = ('message\n'
                           ' message message')
        excepted_error_output = ''

        run_status = run_star_program(input)
        excepted_run_status = RunStatus(input=input,
                                        output=excepted_output,
                                        error_output=excepted_error_output)
        self.assertEqual(run_status, excepted_run_status)


class TestUnitType(unittest.TestCase):
    def setUp(self):
        self.kwargs = self._build_simple_arguments_for_unit_type_constructor()

    def _build_simple_arguments_for_unit_type_constructor(self):
        return {'can_attack':False,
                'vision_radius':2,
                'has_storage':True,
                'storage_size':5,
                'build_cost':2,
                'can_build':False,
                'movable':False,
                'behaviour_when_attacked':BEHAVIOUR_WHEN_ATTACKED.DESTROY,
                'names':['MyUnitType', 'mut']}

    def test_upper_cases_names(self):
        unit_type = UnitType(**self.kwargs)
        self.assertEqual(unit_type.main_name, 'myunittype')

    def test_deep_copy(self):
        unit_type = UnitType(**self.kwargs)
        unit_type_copy = copy.deepcopy(unit_type)
        self.assertEqual(unit_type, unit_type_copy)

    def test_unit_type_must_have_names(self):
        self.kwargs['names'] = []
        illegal_operation = lambda: UnitType(**self.kwargs)
        self.assertRaises(ValueError, illegal_operation)


class TestLoadGameMap(unittest.TestCase):
    def test_basic(self):
        data = ("This is scriptcraft map version 1.\n"
                ". ; ^ _ \n"
                "@ , # ~ \n"
                ".M;T^S_T\n"
                "@S,M# ~ \n")

        game_map = load_game_map(data)

        for i in xrange(16):
            self.assertEqual(game_map[i%4, i/4].ground_type, (i%8)+1)
        self.assertTrue(isinstance(game_map[1, 2].maybe_object, Tree))
        self.assertTrue(isinstance(game_map[3, 2].maybe_object, Tree))
        self.assertTrue(isinstance(game_map[0, 2].maybe_object,
                                   MineralDeposit))
        self.assertTrue(isinstance(game_map[1, 3].maybe_object,
                                   MineralDeposit))
        self.assertTrue(game_map[0, 2].maybe_object.minerals, 50)
        self.assertTrue(game_map[1, 3].maybe_object.minerals, 50)
        self.assertEqual(game_map._free_start_positions,
                         set([(0, 3), (2, 2)]))

    def test_invalid_input(self):
        data = 'Invalid input'

        illegal_operation = lambda: load_game_map(data)
        self.assertRaises(InvalidGameMapData, illegal_operation)
