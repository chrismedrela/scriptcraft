#!/usr/bin/env python
#-*- coding:utf-8 -*-

import random

from scriptcraft.core import actions, cmds, direction
from scriptcraft.core import parse
from scriptcraft.core.compileAndRunProgram import CompileAndRunProgram
from scriptcraft.core.FindPathProblem import FindPathProblem
from scriptcraft.core.GameMap import FieldIsOccupied
from scriptcraft.core.Message import Message
from scriptcraft.core.parse import Parse
from scriptcraft.core.Player import Player
from scriptcraft.core.Program import Program, STAR_PROGRAM, run_star_program
from scriptcraft.core.Unit import Unit
from scriptcraft.core.UnitType import BEHAVIOUR_WHEN_ATTACKED
from scriptcraft.utils import *



class InvalidSender(Exception):
    pass


class InvalidReceiver(Exception):
    pass


class CannotStoreMinerals(Exception):
    pass


class Game(object):
    def __init__(self, game_map, game_configuration):
        self.game_map = game_map
        self.units_by_IDs = {}
        self.players_by_IDs = {}
        self.configuration = game_configuration
        self._units_and_players_counter = 0
        self.turn_number = 0
        self.inbox = []
        self.outbox = []

    def new_player(self, name, color):
        """ May raise NoFreeStartPosition """

        start_position = self.game_map.reserve_next_free_start_position()
        ID = self._get_new_ID()
        player = Player(name, color, ID, start_position)

        self.players_by_IDs[player.ID] = player

        return player

    def _get_new_ID(self):
        self._units_and_players_counter += 1
        return self._units_and_players_counter

    def new_player_with_units(self, name, color):
        """ May raise NoFreeStartPosition """

        player = self.new_player(name, color)

        base = self.new_unit(player, player.start_position, self.configuration.main_base_type)
        base.minerals = self.configuration.minerals_for_main_unit_at_start
        player.set_base(base)

        miners = []
        for dx, dy in direction.FROM_RAY:
            position = player.start_position[0] + dx, player.start_position[1] + dy
            miner = self.new_unit(player, position, self.configuration.main_miner_type)
            miners.append(miner)

        return player, base, miners

    def new_unit(self, player, position, unit_type):
        if not self.game_map.get_field(position).is_empty():
            raise FieldIsOccupied()

        ID = self._get_new_ID()
        unit = Unit(player, unit_type, position, ID)
        player.add_unit(unit)

        self.game_map.place_unit_at(position, ID)
        self.units_by_IDs[unit.ID] = unit

        return unit

    def remove_unit(self, unit):
        unit.player.remove_unit(unit)
        del self.units_by_IDs[unit.ID]
        self.game_map.erase_at(unit.position)

    def move_unit_at(self, unit, new_position):
        if not self.game_map.get_field(new_position).is_empty():
            raise FieldIsOccupied()

        self.game_map.erase_at(unit.position)
        self.game_map.place_unit_at(new_position, unit.ID)
        unit.position = new_position

    def set_program(self, unit, program):
        assert (isinstance(program, Program)
                or program == STAR_PROGRAM
                or program is None)
        unit.program = program

    def fire_at(self, position):
        field = self.game_map.get_field(position)

        if field.has_trees():
            self.game_map.erase_at(position)

        elif field.has_unit():
            self._fire_at_unit(field)

        else:
            pass

    def _fire_at_unit(self, field):
        def destroy():
            self.remove_unit(unit)

        def get_mineral_or_destroy():
            if unit.minerals == 0:
                self.remove_unit(unit)

            else:
                unit.minerals -= 1

        unit_ID = field.get_unit_ID()
        unit = self.units_by_IDs[unit_ID]
        switch = {BEHAVIOUR_WHEN_ATTACKED.DESTROY : destroy,
                  BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY : get_mineral_or_destroy}

        case = switch[unit.type.behaviour_when_attacked]
        case()

    def store_minerals_from_deposit_to_unit(self, source_position, destination):
        field_with_source = self.game_map.get_field(source_position)
        if field_with_source.get_minerals() == 0:
            raise CannotStoreMinerals('source (mineral deposit) is empty')

        if destination.minerals == destination.type.storage_size:
            raise CannotStoreMinerals('destination unit is full')

        minerals_in_source = field_with_source.get_minerals()
        self.game_map.erase_at(source_position)
        self.game_map.place_minerals_at(source_position, minerals_in_source-1)

        destination.minerals += 1

    def store_minerals_from_unit_to_unit(self, source, destination):
        if source.minerals == 0:
            raise CannotStoreMinerals('source unit is empty')

        if destination.minerals == destination.type.storage_size:
            raise CannotStoreMinerals('destination unit is full')

        source.minerals -= 1
        destination.minerals += 1

    def tic(self, folder):
        self._tic_for_world()
        self._compile_and_run_programs(folder)
        self._clear_mailboxes()
        self._analise_outputs()
        self._validate_and_send_messages()
        self._reply_system_messages()
        self._execute_commands()

    def _compile_and_run_programs(self, folder):
        for unit in self.units_by_IDs.itervalues():
            input = self._generate_input_for(unit)

            if isinstance(unit.program, Program):
                e = CompileAndRunProgram(unit.program, input, folder)
                if e.maybe_compilation_status:
                    unit.maybe_last_compilation_status = e.maybe_compilation_status
                unit.maybe_run_status = e.maybe_running_status

            elif unit.program == STAR_PROGRAM:
                unit.maybe_run_status = run_star_program(input)

            else:
                unit.maybe_run_status = None

    def _analise_outputs(self):
        for unit in self.units_by_IDs.itervalues():
            if unit.maybe_run_status:
                parser = Parse(unit.maybe_run_status.output)
                messages = [Message(sender_ID=unit.ID,
                                    receiver_ID=stub[0],
                                    text=stub[1])
                            for stub in parser.message_stubs]
                commands = parser.commands

            else:
                messages = []
                commands = [cmds.StopCommand()]

            unit.command = commands[-1] if commands else cmds.StopCommand()
            unit.outbox_queue = messages

    def _validate_and_send_messages(self):
        def can_be_sent_by(message, unit):
            receiver = self.units_by_IDs.get(message.receiver_ID, None)
            return ((receiver != None and receiver.player == unit.player)
                    or message.receiver_ID == 0)

        for unit in self.units_by_IDs.itervalues():
            for message in unit.outbox_queue:
                if can_be_sent_by(message, unit):
                    self._send_message(message)

    def _reply_system_messages(self):
        for message in self.inbox:
            reply = self._generate_answer_to_system_message(message)
            if reply:
                self._send_message(reply)

    def _execute_commands(self):
        units_IDs = self.units_by_IDs.keys()
        random.shuffle(units_IDs)

        for unit_ID in units_IDs:
            unit = self.units_by_IDs.get(unit_ID, None)

            if not unit:
                continue

            unit.action = self._generate_action_for(unit)
            self._execute_action_for(unit)

    def _send_message(self, message):
        is_valid_ID = lambda ID: ID in self.units_by_IDs or ID == 0

        if not is_valid_ID(message.sender_ID):
            raise InvalidSender()

        if not is_valid_ID(message.receiver_ID):
            raise InvalidReceiver()

        sender = self if message.sender_ID == 0 else self.units_by_IDs[message.sender_ID]
        sender.outbox.append(message)

        receiver = self if message.receiver_ID == 0 else self.units_by_IDs[message.receiver_ID]
        receiver.inbox.append(message)

    def _clear_mailboxes(self):
        def clear_mailbox_of(obj):
            obj.inbox = []
            obj.outbox = []

        clear_mailbox_of(self)

        for unit in self.units_by_IDs.itervalues():
            clear_mailbox_of(unit)

    def _generate_answer_to_system_message(self, message):
        def list_units():
            sender = self.units_by_IDs[message.sender_ID]
            player = sender.player
            text = "%d " % len(player.units)
            text += " ".join(map(lambda unit: "%d %s" % (unit.ID, unit.type.main_name),
                                  player.units))
            return text

        def unit_info():
            unit_ID = parse._parse_as_int(split_text[1])
            if unit_ID == None:
                return None

            unit = self.units_by_IDs.get(unit_ID, None)
            if unit == None:
                return None

            text_dict = {'ID':unit.ID,
                         'type':unit.type.main_name,
                         'x':unit.position[0],
                         'y':unit.position[1],
                         'more_info': unit.minerals if unit.type.storage_size != 0 else unit.type.attack_range}
            text = "%(ID)d %(type)s %(x)d %(y)d %(more_info)d" % text_dict
            return text

        cleaned_text = message.text.lower()
        split_text = tuple(cleaned_text.split())

        if split_text == ('list', 'units') or split_text == ('lu',):
            case = list_units
        elif split_text[0] in ('unit', 'u') and len(split_text)==2:
            case = unit_info
        else:
            return None

        response_text = case()
        if response_text == None:
            return None

        response = Message(sender_ID=0,
                           receiver_ID=message.sender_ID,
                           text=response_text)
        return response

    def _generate_input_for(self, unit):
        # first line of info
        input_data_dict = {'type':unit.type.main_name,
                           'ID':unit.ID,
                           'player_ID':unit.player.ID,
                           'messages_len':len(unit.inbox),
                           'x':unit.position[0],
                           'y':unit.position[1],
                           'vision_diameter':unit.type.vision_diameter,
                           'extra_info': unit.minerals if unit.type.storage_size!=0 else unit.type.attack_range}
        input_data = '%(type)s %(ID)d %(player_ID)d %(messages_len)d %(x)d %(y)d %(vision_diameter)d\n%(extra_info)d\n' % input_data_dict

        # info about surroundings
        def generate_input_for_field(x, y):
            # out of map?
            if not self.game_map.is_valid_position((x, y)):
                return '1 0 0'

            # not out of map
            field = self.game_map[x][y]

            if field.is_empty():
                if field.is_flat():
                    return '0 0 0'
                else: # is upland
                    return '1 0 0'

            elif field.has_mineral_deposit():
                minerals = field.get_minerals()
                return '2 %d 0' % minerals

            elif field.has_trees():
                return '3 0 0'

            else:
                assert field.has_unit()

                unit_ID = field.get_unit_ID()
                unit = self.units_by_IDs[unit_ID]
                unit_type = unit.type.main_name
                player_ID = unit.player.ID
                return '%s %d %d' % (unit_type, unit_ID, player_ID)


        input_data += '\n'.join(map(' '.join,
                                    [   [   generate_input_for_field(x, y)
                                        for x in xrange(unit.position[0] - unit.type.vision_radius,
                                                        unit.position[0] + unit.type.vision_radius + 1)]
                                    for y in xrange(unit.position[1] - unit.type.vision_radius,
                                                    unit.position[1] + unit.type.vision_radius + 1)]))
        input_data += '\n'

        # messages
        input_data += '\n'.join(map(lambda message: '%d %s' % (message.sender_ID,
                                                               message.text),
                                    unit.inbox))

        return input_data

    def find_nearest_unit_in_range_fulfilling_condition(self, center, range, condition):
        def positions_in_range(center, range):
            for x in xrange(center[0]-range,
                            center[0]+range+1):
                for y in xrange(center[1]-range,
                                center[1]+range+1):
                    if distance((x, y), center) <= range:
                        yield x, y

        valid_fields = (self.game_map.get_field(pos)
                        for pos in positions_in_range(center, range)
                        if self.game_map.is_valid_position(pos))
        units = (self.units_by_IDs[field.get_unit_ID()]
                 for field in valid_fields
                 if field.has_unit())
        units_fulfilling_condition = filter(lambda unit: condition(unit),
                                            units)
        the_nearest = (None
                       if not units_fulfilling_condition
                       else min(units_fulfilling_condition,
                                key=lambda unit: distance(center, unit.position)))

        return the_nearest

    def _generate_action_for(self, unit):
        command_type = type(unit.command)

        switch = {cmds.StopCommand : self._generate_action_for_unit_with_stop_command,
                  cmds.ComplexMoveCommand : self._generate_action_for_unit_with_complex_move_command,
                  cmds.MoveCommand : self._generate_action_for_unit_with_move_command,
                  cmds.ComplexGatherCommand : self._generate_action_for_unit_with_complex_gather_command,
                  cmds.FireCommand : self._generate_action_for_unit_with_fire_command,
                  cmds.ComplexAttackCommand : self._generate_action_for_unit_with_complex_attack_command,
                  cmds.BuildCommand : self._generate_action_for_unit_with_build_command}
        case = switch[command_type]

        return case(unit)

    def _generate_action_for_unit_with_stop_command(self, unit):
        return actions.StopAction()

    def _generate_action_for_unit_with_complex_move_command(self, unit):
        if not unit.type.movable:
            return actions.StopAction()

        if not self.game_map.is_valid_position(unit.command.destination):
            return actions.StopAction()

        return self._find_path_and_generate_action(unit)

    def _generate_action_for_unit_with_move_command(self, unit):
        command = unit.command
        ray = direction.TO_RAY[command.direction]
        destination = (ray[0] + unit.position[0],
                       ray[1] + unit.position[1])
        unit_type = unit.type

        if not unit_type.movable:
            return actions.StopAction()

        if not self.game_map.is_valid_position(destination):
            return actions.StopAction()

        if not self.game_map.get_field(destination).is_empty():
            return actions.StopAction()

        return actions.MoveAction(source=unit.position,
                                  destination=destination)

    def _generate_action_for_unit_with_complex_gather_command(self, unit):
        if not unit.type.movable or not unit.type.has_storage:
            return actions.StopAction()

        destination = unit.command.destination
        if not self.game_map.is_valid_position(destination):
            return actions.StopAction()

        destination_field = self.game_map.get_field(destination)
        if not destination_field.has_mineral_deposit():
            return actions.StopAction()

        if unit.minerals == unit.type.storage_size:
            if not unit.player.maybe_base:
                return actions.StopAction()

            base = unit.player.maybe_base

            if distance(unit.position, base.position) == 1:
                # store
                if base.minerals == base.type.storage_size:
                    return actions.StopAction()

                else:
                    return actions.StoreAction(storage_ID=base.ID)

            else:
                # go to base
                return self._find_path_and_generate_action(unit, goal=base.position)

        else:
            if distance(unit.position, destination) == 1:
                # gather
                if destination_field.get_minerals() == 0:
                    return actions.StopAction()

                else:
                    return actions.GatherAction(source=destination)

            else:
                # go to mineral deposit
                return self._find_path_and_generate_action(unit, goal=destination)

    def _generate_action_for_unit_with_fire_command(self, unit):
        if not unit.type.can_attack:
            return actions.StopAction()

        destination = unit.command.destination
        if not self.game_map.is_valid_position(destination):
            return actions.StopAction()

        if distance(unit.position, destination) > unit.type.attack_range:
            return actions.StopAction()

        if unit.position == destination:
            return actions.StopAction()

        return actions.FireAction(destination)

    def _generate_action_for_unit_with_complex_attack_command(self, unit):
        if not unit.type.movable or not unit.type.can_attack:
            return actions.StopAction()

        if not self.game_map.is_valid_position(unit.command.destination):
            return actions.StopAction()

        destination_field = self.game_map.get_field(unit.command.destination)

        alien_on_destination_field = False
        if destination_field.has_unit():
            unit_on_destination_field = self.units_by_IDs[destination_field.get_unit_ID()]
            if unit_on_destination_field.player != unit.player:
                alien_on_destination_field = True

        if alien_on_destination_field:
            # attack alien on destination field
            return actions.FireAction(destination=unit.command.destination)

        else:
            maybe_nearest_alien_in_attack_range = \
                self.find_nearest_unit_in_range_fulfilling_condition( \
                    unit.position, unit.type.attack_range,
                    lambda u: u.player != unit.player)

            if maybe_nearest_alien_in_attack_range:
                # attack alien in attack range
                alien = maybe_nearest_alien_in_attack_range
                return actions.FireAction(destination=alien.position)

            else:
                # no aliens in attack range ==> move to destination
                return self._find_path_and_generate_action(unit)

    def _generate_action_for_unit_with_build_command(self, unit):
        if not unit.type.can_build:
            return actions.StopAction()

        type_name = unit.command.unit_type_name
        new_unit_type = self.configuration.units_types_by_names.get(type_name, None)

        if not new_unit_type:
            return actions.StopAction()

        if not new_unit_type.can_be_built:
            return actions.StopAction()

        if (new_unit_type.build_cost > unit.minerals
            if unit.type.has_storage
            else new_unit_type.build_cost != 0):
            return actions.StopAction()

        # find free neightbour
        maybe_free_position = self.game_map.find_flat_and_free_neighbour_of(unit.position)

        if not maybe_free_position:
            return actions.StopAction()
        position = maybe_free_position

        # build unit
        if unit.type.has_storage:
            unit.minerals -= new_unit_type.build_cost

        return actions.BuildAction(unit_type=new_unit_type,
                                   destination=position)

    def _find_path_and_generate_action(self, unit, goal=None):
        source = unit.position
        goal = goal or unit.command.destination
        problem = FindPathProblem(source, goal, self.game_map)
        maybe_direction = problem.find_direction()
        if not maybe_direction:
            return actions.StopAction()

        ray = direction.TO_RAY[maybe_direction]
        destination = (ray[0] + source[0],
                       ray[1] + source[1])
        return actions.MoveAction(source=unit.position,
                                 destination=destination)

    def _execute_action_for(self, unit):
        action_type = type(unit.action)

        switch = {
            actions.StopAction : \
                lambda: None,
            actions.MoveAction : \
                lambda: self.move_unit_at(unit,
                                          unit.action.destination),
            actions.GatherAction : \
                lambda: self.store_minerals_from_deposit_to_unit(unit.action.source,
                                                                 unit),
            actions.StoreAction : \
                lambda: self.store_minerals_from_unit_to_unit(unit,
                                                              self.units_by_IDs[unit.action.storage_ID]),
            actions.FireAction : \
                lambda: self.fire_at(unit.action.destination),
            actions.BuildAction : \
                lambda: self.new_unit(unit.player,
                                      unit.action.destination,
                                      unit.action.unit_type)}

        case = switch[action_type]
        case()

    def _tic_for_world(self):
        for x in xrange(self.game_map.size[0]):
            for y in xrange(self.game_map.size[1]):
                if self.game_map[x][y].has_mineral_deposit():
                    if random.random() < self.configuration.probability_of_mineral_deposit_growing:
                        minerals = self.game_map[x][y].get_minerals()
                        self.game_map.erase_at((x, y))
                        self.game_map.place_minerals_at((x, y), minerals+1)
