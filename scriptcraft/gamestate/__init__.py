#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Following actions are available:

StopAction
MoveAction
GatherAction
StoreAction
FireAction
BuildAction

"""
"""
Classes *Command represent commands of units. Following command are available:
 StopCommand
 MoveCommand
 ComplexMoveCommand
 ComplexGatherCommand
 FireCommand
 ComplexAttackCommand
 BuildCommand

Attributes of instances of these classes must be accurate type, but
haven't be sensible (for example every string is valid value for unit_type_name).

"""



from collections import namedtuple
import random

from scriptcraft import direction
from scriptcraft.compilation import CompileAndRunProgram
from scriptcraft.gamemap import FieldIsOccupied, FindPathProblem
from scriptcraft.gamestate import cmds, actions
from scriptcraft.parser import Parser
from scriptcraft.utils import *



class InvalidSender(Exception):
    pass


class InvalidReceiver(Exception):
    pass


class CannotStoreMinerals(Exception):
    pass


_parser = Parser(cmds.ALL_COMMANDS)


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

    @log_on_enter('tic method in Game', mode='time')
    def tic(self, compile_and_run_function):
        self._tic_for_world()
        self._compile_and_run_programs(compile_and_run_function)
        self._clear_mailboxes()
        self._analise_outputs()
        self._validate_and_send_messages()
        self._reply_system_messages()
        self._execute_commands()

    @log_on_enter('compile and run all programs', mode='time')
    def _compile_and_run_programs(self, compile_and_run_function):
        for unit in self.units_by_IDs.itervalues():
            input = self._generate_input_for(unit)

            if isinstance(unit.program, Program):
                status = compile_and_run_function(unit.program.language,
                                                  unit.program.code,
                                                  input)
                maybe_compilation_status, maybe_running_status = status
                if maybe_compilation_status:
                    output, error_output = maybe_compilation_status
                    compilation_status = CompilationStatus(output, error_output)
                    unit.maybe_last_compilation_status = compilation_status
                if maybe_running_status:
                    output, error_output = maybe_running_status
                    running_status = RunStatus(input, output, error_output)
                    unit.maybe_run_status = running_status
                else:
                    unit.maybe_run_status = None

            elif unit.program == STAR_PROGRAM:
                unit.maybe_run_status = run_star_program(input)

            else:
                unit.maybe_run_status = None

    @log_on_enter('analising outputs', mode='time')
    def _analise_outputs(self):
        for unit in self.units_by_IDs.itervalues():
            if unit.maybe_run_status:
                message_stubs, commands = \
                  _parser.parse(unit.maybe_run_status.output)
                messages = [Message(sender_ID=unit.ID,
                                    receiver_ID=stub[0],
                                    text=stub[1])
                            for stub in message_stubs]
                commands = commands

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

    @log_on_enter('execute commands', mode='time')
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
            def _parse_as_int(data):
                """ Return int or None if data is invalid. """

                if len(data)>9:
                    return None
                try:
                    return int(data)
                except ValueError:
                    return None

            unit_ID = _parse_as_int(split_text[1])
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
        elif len(split_text)==2 and split_text[0] in ('unit', 'u'):
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

    @log_on_enter('generating input', mode='only time')
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

    @log_on_enter('find nearest unit in range', mode='only time')
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

        def build_unit():
            new_unit = self.new_unit(unit.player,
                                 unit.action.destination,
                                 unit.action.unit_type)
            self.set_program(new_unit, unit.program)

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
                build_unit
        }

        case = switch[action_type]
        case()

    @log_on_enter('tic for world', mode='time')
    def _tic_for_world(self):
        for x in xrange(self.game_map.size[0]):
            for y in xrange(self.game_map.size[1]):
                if self.game_map[x][y].has_mineral_deposit():
                    if random.random() < self.configuration.probability_of_mineral_deposit_growing:
                        minerals = self.game_map[x][y].get_minerals()
                        self.game_map.erase_at((x, y))
                        self.game_map.place_minerals_at((x, y), minerals+1)


class Unit(object):
    def __init__(self, player, type, position, ID):
        self.program = None
        self.maybe_last_compilation_status = None
        self.maybe_run_status = None
        self.command = cmds.StopCommand()
        self.action = actions.StopAction()
        self.position = position
        self.player = player
        self.ID = ID
        self.type = type
        self._minerals = 0
        self.outbox = []
        self.inbox = []

    @ property
    def minerals(self):
        return self._minerals

    @ minerals.setter
    def minerals(self, value):
        assert value >= 0
        assert value <= self.type.storage_size or not self.type.has_storage_limit
        self._minerals = value

    def __str__(self):
        return ("<Unit:%d | " % self.ID) + \
               ("%s of player %d " % (self.type.main_name, self.player.ID)) + \
               ("at (%d, %d) " % (self.position[0], self.position[1])) + \
               ("with %d minerals " % self.minerals if self.type.has_storage else "") + \
               ("%s " % (("with %s" % (self.program,))
                         if self.program else "without program")) + \
               ("with %s doing %s>" % (self.command, self.action))


class BEHAVIOUR_WHEN_ATTACKED(object):
    DESTROY = '<Enum: destroy>'
    GET_MINERAL_OR_DESTROY = '<Enum: get mineral or destroy>'


def _use_default_value_if_flag_is_False(kwargs, flag_name, attribute_name, default_value):
    if flag_name in kwargs:
        if not kwargs[flag_name]:
            assert kwargs.get(attribute_name, default_value) == default_value
            kwargs[attribute_name] = default_value
        else:
            assert attribute_name in kwargs
        del kwargs[flag_name]


class UnitType(namedtuple('UnitType', ('attack_range',
                                       'vision_radius',
                                       'storage_size',
                                       'build_cost',
                                       'can_build',
                                       'movable',
                                       'behaviour_when_attacked',
                                       'names'))):
    """
    Attributes:
    attack_range -- value 0 means unit cannot attack
    can_attack -- if False then attack_range == 0
    vision_radius -- 0 is valid value
    vision_diameter -- computed from vision_radius; not allowed in __init__ args
    storage_size -- value -1 means there is no limit
    has_storage -- if False then store_size == 0
    build_cost -- 0 is valid value; it hasn't sense when buildable==False
    can_be_built -- if False then build_cost == -1
    can_build
    movable
    behaviour_when_attacked -- enum BEHAVIOUR_WHEN_ATTACKED
    names -- non-empty list or tuple (always lowercase); the first name is main name
    main_name -- not allowed in __init__ args - it's the first name from names

    """

    __slots__ = ()

    @ copy_if_an_instance_given
    def __new__(cls, **kwargs):
        _use_default_value_if_flag_is_False(kwargs, 'can_be_built', 'build_cost', -1)
        _use_default_value_if_flag_is_False(kwargs, 'has_storage', 'storage_size', 0)
        _use_default_value_if_flag_is_False(kwargs, 'can_attack', 'attack_range', 0)

        if len(kwargs['names']) == 0:
            raise ValueError('unit type must have at least one name')

        kwargs['names'] = map(lambda x: x.lower(),
                              kwargs['names'])

        return cls.__bases__[0].__new__(cls, **kwargs)

    def __deepcopy__(self, memo):
        c = UnitType(self)
        return c

    @ property
    def main_name(self):
        return self.names[0]

    @ property
    def vision_diameter(self):
        return 2*self.vision_radius + 1

    @ property
    def can_be_built(self):
        return self.build_cost != -1

    @ property
    def has_storage(self):
        return self.storage_size != 0

    @ property
    def has_storage_limit(self):
        return self.storage_size != -1

    @ property
    def can_attack(self):
        return self.attack_range != 0


DEFAULT_MINER_TYPE = UnitType(
    attack_range=0,
    vision_radius=7,
    storage_size=1,
    build_cost=3,
    can_build=False,
    movable=True,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
    names=('5', 'miner', 'm')
)
DEFAULT_BASE_TYPE = UnitType(
    attack_range=0,
    vision_radius=16,
    has_storage=True,
    storage_size= -1,
    can_be_built=False,
    can_build=True,
    movable=False,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY,
    names=('4', 'base', 'b')
)
DEFAULT_TANK_TYPE = UnitType(
    can_attack=True,
    attack_range=3,
    vision_radius=7,
    has_storage=False,
    build_cost=10,
    can_build=False,
    movable=True,
    behaviour_when_attacked=BEHAVIOUR_WHEN_ATTACKED.DESTROY,
    names=('6', 'tank', 't')
)


class GameConfiguration(namedtuple("GameConfiguration",
    ('units_types_by_names',
     'main_base_type',
     'main_miner_type',
     'minerals_for_main_unit_at_start',
     'probability_of_mineral_deposit_growing')
    )):
    __slots__ = ()

    @ copy_if_an_instance_given
    def __new__(cls,
                units_types,
                main_base_type,
                main_miner_type,
                minerals_for_main_unit_at_start,
                probability_of_mineral_deposit_growing,):

        units_types_by_names = {}
        for unit_type in units_types:
            for name in unit_type.names:
                if name in units_types_by_names:
                    raise ValueError("Units types with the same names are not allowed.")
                units_types_by_names[name] = unit_type

        if main_base_type not in units_types or main_miner_type not in units_types:
            raise ValueError("main_base_type or main_miner_type not in units_types")

        return cls.__bases__[0].__new__(cls,
                                        units_types_by_names,
                                        main_base_type,
                                        main_miner_type,
                                        minerals_for_main_unit_at_start,
                                        probability_of_mineral_deposit_growing)

    def __deepcopy__(self, memo):
        c = GameConfiguration(self)
        return c


DEFAULT_GAME_CONFIGURATION = GameConfiguration(
    units_types=[DEFAULT_BASE_TYPE,
                 DEFAULT_MINER_TYPE,
                 DEFAULT_TANK_TYPE],
    main_base_type=DEFAULT_BASE_TYPE,
    main_miner_type=DEFAULT_MINER_TYPE,
    minerals_for_main_unit_at_start=10,
    probability_of_mineral_deposit_growing=0.1,
)


class Player(object):
    def __init__(self, name, color, ID, start_position):
        self.name = name
        self.color = color
        self.ID = ID
        self.units = []
        self.maybe_base = None
        self.start_position = start_position

    def add_unit(self, unit):
        unit.player = self
        self.units.append(unit)

    def set_base(self, unit):
        assert unit in self.units
        self.maybe_base = unit

    def remove_unit(self, unit):
        unit.player = None
        self.units.remove(unit)
        if self.maybe_base == unit:
            self.maybe_base = None

    def __str__(self):
        return ("<Player:%d | "
                "color (%d, %d, %d) "
                "started at (%d, %d) "
                "with units {%s}") \
                % (self.ID,
                   self.color[0], self.color[1], self.color[2],
                   self.start_position[0], self.start_position[1],
                   ", ".join(map(lambda unit: str(unit.ID), self.units)))


STAR_PROGRAM = Const('star program')
def run_star_program(input):
    commands = []
    lines = iter(input.split('\n'))
    try:
        splited_first_line = lines.next().split()
        vision_diameter = int(splited_first_line[6])
        lines.next() # skip parameter
        for i in xrange(vision_diameter):
            lines.next() # skip description of surroundings
        for line in lines:
            line = line.strip()
            splited = line.split(None, 1)
            if len(splited) == 2:
                command = line[len(splited[0])+1:]
                commands.append(command)
    except (StopIteration, ValueError, IndexError):
        pass
    """
    for line in input.split('\n'):
        splited = line.strip().split(None, 1)
        if len(splited) == 2:
            maybe_number = splited[0]
            if len(maybe_number)<9:
                try:
                    int(maybe_number)
                except ValueError:
                    pass
                else:
                    command = line[len(maybe_number)+1:]
                    commands.append(command)
    """
    output = "\n".join(commands)

    return RunStatus(input=input,
                         output=output,
                         error_output='')


class Program(namedtuple("Program", ('language',
                                     'code'))):
    __slots__ = ()

    @ property
    def _code_sha(self):
        sha = hashlib.sha1()
        sha.update(self.code)
        sha = sha.hexdigest()
        return sha

    def __str__(self):
        return "<Program in %s with code sha = %s>" \
               % (self.language, self._code_sha)


class CompilationStatus(namedtuple("CompilationStatus",
                                   ('output', 'error_output'))):
    __slots__ = ()


class RunStatus(namedtuple("RunStatus", ('input',
                                        'output',
                                        'error_output'))):
    __slots__ = ()


class Language(object):
    CPP = 'cpp'
    PYTHON = 'py'


class Message(namedtuple('Message', ('sender_ID',
                                     'receiver_ID',
                                     'text'))):
    """ Attributes 'sender_ID' and 'receiver_ID' might be equal to
    zero. It means that the sender/receiver is game system. """

    __slots__ = ()

