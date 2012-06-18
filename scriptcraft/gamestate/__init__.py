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
import hashlib
import random

from scriptcraft import direction
from scriptcraft.compilation import CompileAndRunProgram
from scriptcraft.gamemap import FieldIsOccupied, GameMap
from scriptcraft.gamestate import cmds, actions
from scriptcraft.parser import Parser, parse_system_question
from scriptcraft.utils import *



class InvalidSender(Exception):
    pass


class InvalidReceiver(Exception):
    pass


class CannotStoreMinerals(Exception):
    pass


class NoFreeStartPosition(Exception):
    pass


class InvalidGameMapData(Exception):
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

        start_position = self.game_map.try_reserve_free_start_position()
        if start_position is None:
            raise NoFreeStartPosition()
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

        base = self.new_unit(player, player.start_position,
                             self.configuration.main_base_type)
        base.minerals = self.configuration.minerals_for_main_unit_at_start
        player.set_base(base)

        miners = []
        for dx, dy in direction.FROM_RAY:
            position = (player.start_position[0] + dx,
                        player.start_position[1] + dy)
            miner = self.new_unit(player, position,
                                  self.configuration.main_miner_type)
            miners.append(miner)

        return player, base, miners

    def new_unit(self, player, position, unit_type):
        field = self.game_map[position]
        assert field.valid_position, 'invalid position %r' % (position,)
        if not field.empty:
            raise FieldIsOccupied()

        ID = self._get_new_ID()
        unit = Unit(player, unit_type, position, ID)
        player.add_unit(unit)

        self.game_map[position].place_object(unit)
        self.units_by_IDs[unit.ID] = unit

        return unit

    def remove_unit(self, unit):
        unit.player.remove_unit(unit)
        del self.units_by_IDs[unit.ID]
        self.game_map[unit.position].place_object(None)

    def move_unit_at(self, unit, new_position):
        field = self.game_map[new_position]
        assert field.valid_position, 'invalid position %r' % (position,)
        if not field.empty:
            raise FieldIsOccupied()

        self.game_map[unit.position].place_object(None)
        self.game_map[new_position].place_object(unit)
        unit.position = new_position

    def set_program(self, unit, program):
        assert (isinstance(program, Program)
                or program == STAR_PROGRAM
                or program is None)
        unit.program = program

    def fire_at(self, position):
        assert self.game_map[position].valid_position, \
          'invalid position %r' % (position, )

        maybe_object = self.game_map[position].maybe_object

        if isinstance(maybe_object, Tree):
            self.game_map[position].place_object(None)

        elif isinstance(maybe_object, Unit):
            self._fire_at_unit(maybe_object)

        else: # MineralDeposit or None
            pass

    def _fire_at_unit(self, unit):
        def destroy():
            self.remove_unit(unit)

        def get_mineral_or_destroy():
            if unit.minerals == 0:
                self.remove_unit(unit)

            else:
                unit.minerals -= 1

        switch = {BEHAVIOUR_WHEN_ATTACKED.DESTROY : destroy,
                  BEHAVIOUR_WHEN_ATTACKED.GET_MINERAL_OR_DESTROY : get_mineral_or_destroy}

        case = switch[unit.type.behaviour_when_attacked]
        case()

    def store_minerals_from_deposit_to_unit(self, source_position,
                                            destination_unit):
        mineral_deposit = self.game_map[source_position].maybe_object
        if mineral_deposit.minerals == 0:
            raise CannotStoreMinerals('source (mineral deposit) is empty')

        if destination_unit.minerals == destination_unit.type.storage_size:
            raise CannotStoreMinerals('destination_unit unit is full')

        mineral_deposit.minerals -= 1
        destination_unit.minerals += 1

    def store_minerals_from_unit_to_unit(self, source_unit,
                                         destination_unit):
        if source_unit.minerals == 0:
            raise CannotStoreMinerals('source_unit unit is empty')

        if destination_unit.minerals == destination_unit.type.storage_size:
            raise CannotStoreMinerals('destination_unit unit is full')

        source_unit.minerals -= 1
        destination_unit.minerals += 1

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

            # unit can be destroyed by another unit
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

        sender = (self if message.sender_ID == 0
                  else self.units_by_IDs[message.sender_ID])
        sender.outbox.append(message)

        receiver = (self if message.receiver_ID == 0
                    else self.units_by_IDs[message.receiver_ID])
        receiver.inbox.append(message)

    def _clear_mailboxes(self):
        def clear_mailbox_of(obj):
            obj.inbox = []
            obj.outbox = []

        clear_mailbox_of(self)

        for unit in self.units_by_IDs.itervalues():
            clear_mailbox_of(unit)

    def _generate_answer_to_system_message(self, message):
        command, args = parse_system_question(message.text)

        if command == 'list-units':
            sender = self.units_by_IDs[message.sender_ID]
            player = sender.player
            text = "%d " % len(player.units)
            text += " ".join(map(lambda unit: "%d %s" % \
                                   (unit.ID, unit.type.main_name),
                                 player.units))

        elif command == 'unit-info':
            unit_ID = args[0]
            unit = self.units_by_IDs.get(unit_ID, None)
            if unit == None:
                return None

            text_dict = {'ID':unit.ID,
                         'type':unit.type.main_name,
                         'x':unit.position[0],
                         'y':unit.position[1],
                         'more_info': (unit.minerals
                                       if unit.type.storage_size != 0
                                       else unit.type.attack_range)}
            text = "%(ID)d %(type)s %(x)d %(y)d %(more_info)d" % text_dict

        else:
            assert command == 'error'
            return None

        response = Message(sender_ID=0,
                           receiver_ID=message.sender_ID,
                           text=text)
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
                           'extra_info': (unit.minerals
                                          if unit.type.storage_size!=0
                                          else unit.type.attack_range)}
        input_data = ('%(type)s %(ID)d %(player_ID)d %(messages_len)d '
                      '%(x)d %(y)d %(vision_diameter)d\n%(extra_info)d\n' \
                        % input_data_dict)

        # info about surroundings
        def generate_input_for_field(x, y):
            # out of map?
            if not self.game_map[x, y].valid_position:
                return '1 0 0'

            # not out of map
            field = self.game_map[x, y]

            obj = field.maybe_object
            if field.empty:
                return '0 0 0'

            elif isinstance(obj, MineralDeposit):
                minerals = obj.minerals
                return '2 %d 0' % minerals

            elif isinstance(obj, Tree):
                return '3 0 0'

            else:
                assert isinstance(obj, Unit)

                unit = obj
                unit_type = unit.type.main_name
                player_ID = unit.player.ID
                return '%s %d %d' % (unit_type, unit.ID, player_ID)


        min_x = unit.position[0] - unit.type.vision_radius
        max_x = unit.position[0] + unit.type.vision_radius
        min_y = unit.position[1] - unit.type.vision_radius
        max_y = unit.position[1] + unit.type.vision_radius
        input_data += '\n'.join(map(
            ' '.join,
            [   [   generate_input_for_field(x, y)
                for x in xrange(min_x, max_x+1)]
            for y in xrange(min_y, max_y+1)]
        ))
        input_data += '\n'

        # messages
        input_data += '\n'.join('%d %s' % (message.sender_ID, message.text)
                                for message in unit.inbox)

        return input_data

    @log_on_enter('find nearest unit in range', mode='only time')
    def find_nearest_unit_in_range_fulfilling_condition(self, center,
                                                        range, condition):
        def positions_in_range(center, range):
            for x in xrange(center[0]-range,
                            center[0]+range+1):
                for y in xrange(center[1]-range,
                                center[1]+range+1):
                    if distance((x, y), center) <= range:
                        yield x, y

        fields = (self.game_map[pos] for pos
                  in positions_in_range(center, range))
        objs = (field.maybe_object for field
                in fields if not field.empty)
        units_fulfilling_condition = list(
            obj for obj in objs
            if isinstance(obj, Unit) and condition(obj))
        if not units_fulfilling_condition:
            return None

        return min(units_fulfilling_condition,
                   key=lambda unit: distance(center, unit.position))

    def _generate_action_for(self, unit):
        command_type = type(unit.command)

        switch = {
            cmds.StopCommand : \
              self._generate_action_for_unit_with_stop_command,
            cmds.ComplexMoveCommand : \
              self._generate_action_for_unit_with_complex_move_command,
            cmds.MoveCommand : \
              self._generate_action_for_unit_with_move_command,
            cmds.ComplexGatherCommand : \
              self._generate_action_for_unit_with_complex_gather_command,
            cmds.FireCommand : \
              self._generate_action_for_unit_with_fire_command,
            cmds.ComplexAttackCommand : \
              self._generate_action_for_unit_with_complex_attack_command,
            cmds.BuildCommand : \
              self._generate_action_for_unit_with_build_command
        }
        case = switch[command_type]

        return case(unit)

    def _generate_action_for_unit_with_stop_command(self, unit):
        return actions.StopAction()

    def _generate_action_for_unit_with_complex_move_command(self, unit):
        if not unit.type.movable:
            return actions.StopAction()

        if not self.game_map[unit.command.destination].valid_position:
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

        destination_field = self.game_map[destination]
        if not destination_field.accessible:
            return actions.StopAction()

        return actions.MoveAction(source=unit.position,
                                  destination=destination)

    def _generate_action_for_unit_with_complex_gather_command(self, unit):
        if not unit.type.movable or not unit.type.has_storage:
            return actions.StopAction()

        destination = unit.command.destination
        destination_field = self.game_map[destination]
        if not destination_field.valid_position:
            return actions.StopAction()

        mineral_deposit = destination_field.maybe_object
        if not isinstance(mineral_deposit, MineralDeposit):
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
                if mineral_deposit.minerals == 0:
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
        destination_field = self.game_map[destination]
        if not destination_field.valid_position:
            return actions.StopAction()

        if distance(unit.position, destination) > unit.type.attack_range:
            return actions.StopAction()

        # don't allow auto-destruction
        if unit.position == destination:
            return actions.StopAction()

        return actions.FireAction(destination)

    def _generate_action_for_unit_with_complex_attack_command(self, unit):
        if not unit.type.movable or not unit.type.can_attack:
            return actions.StopAction()

        destination_field = self.game_map[unit.command.destination]
        if not destination_field.valid_position:
            return actions.StopAction()

        alien_on_destination_field = False
        if isinstance(destination_field.maybe_object, Unit):
            unit_on_destination_field = destination_field.maybe_object
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
        maybe_empty_neighbour = \
            self.game_map.find_accessible_neighbour_of(unit.position)

        if not maybe_empty_neighbour:
            return actions.StopAction()
        position = maybe_empty_neighbour.position

        # build unit
        if unit.type.has_storage:
            unit.minerals -= new_unit_type.build_cost

        return actions.BuildAction(unit_type=new_unit_type,
                                   destination=position)

    def _find_path_and_generate_action(self, unit, goal=None):
        source = unit.position
        goal = goal or unit.command.destination
        maybe_direction = self.game_map.find_direction(source, goal)
        if not maybe_direction:
            return actions.StopAction()

        ray = direction.TO_RAY[maybe_direction]
        destination = (ray[0] + source[0],
                       ray[1] + source[1])
        return actions.MoveAction(source=unit.position,
                                  destination=destination)

    def _execute_action_for(self, unit):
        action_type = type(unit.action)

        def move_action():
            self.move_unit_at(unit, unit.action.destination)
            unit.direction = direction.estimated( \
              unit.action.source, unit.action.destination)

        def gather_action():
            self.store_minerals_from_deposit_to_unit( \
              unit.action.source, unit)
            unit.direction = direction.estimated( \
              unit.position, unit.action.source)

        def store_action():
            storage = self.units_by_IDs[unit.action.storage_ID]
            self.store_minerals_from_unit_to_unit(unit, storage)
            unit.direction = direction.estimated( \
              unit.position, storage.position)

        def fire_action():
            self.fire_at(unit.action.destination)
            unit.direction = direction.estimated( \
              unit.position, unit.action.destination)

        def build_unit():
            new_unit = self.new_unit(unit.player,
                                     unit.action.destination,
                                     unit.action.unit_type)
            self.set_program(new_unit, unit.program)

        switch = {
            actions.StopAction : lambda: None,
            actions.MoveAction : move_action,
            actions.GatherAction : gather_action,
            actions.StoreAction : store_action,
            actions.FireAction : fire_action,
            actions.BuildAction : build_unit,
        }

        case = switch[action_type]
        case()

    @log_on_enter('tic for world', mode='time')
    def _tic_for_world(self):
        for x in xrange(self.game_map.size[0]):
            for y in xrange(self.game_map.size[1]):
                if (isinstance(self.game_map[x, y].maybe_object,
                               MineralDeposit) and
                    random.random() < \
                    self.configuration.probability_of_mineral_deposit_growing):
                    mineral_deposit = self.game_map[x, y].maybe_object
                    mineral_deposit.minerals += 1


class MineralDeposit(object):
    __slots__ = ('_minerals', )

    def __init__(self, minerals):
        self.minerals = minerals

    @property
    def minerals(self):
        return self._minerals

    @minerals.setter
    def minerals(self, value):
        assert value >= 0
        self._minerals = value


class Tree(object):
    MIN_TREE_TYPE = 1
    MAX_TREE_TYPE = 6
    __slots__ = ('type', )

    def __init__(self, type=None):
        type = type or random.randint(Tree.MIN_TREE_TYPE,
                                      Tree.MAX_TREE_TYPE)
        self.type = type


class Unit(object):
    def __init__(self, player, type, position, ID):
        self.direction = direction.N
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
               ("with %s doing %s " % (self.command, self.action)) + \
               ("directed to %s>" % (direction.TO_FULL_NAME[self.direction],))


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


class UnitType(object):
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

    __slots__ = ('attack_range',
                 'vision_radius',
                 'storage_size',
                 'build_cost',
                 'can_build',
                 'movable',
                 'behaviour_when_attacked',
                 'names')

    def __init__(self, **kwargs):
        _use_default_value_if_flag_is_False(kwargs, 'can_be_built', 'build_cost', -1)
        _use_default_value_if_flag_is_False(kwargs, 'has_storage', 'storage_size', 0)
        _use_default_value_if_flag_is_False(kwargs, 'can_attack', 'attack_range', 0)

        if len(kwargs['names']) == 0:
            raise ValueError('unit type must have at least one name')

        kwargs['names'] = map(lambda x: x.lower(),
                              kwargs['names'])

        for k, v in kwargs.items():
            setattr(self, k, v)

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


class GameConfiguration(object):
    __slots__ = ('units_types_by_names',
                 'main_base_type',
                 'main_miner_type',
                 'minerals_for_main_unit_at_start',
                 'probability_of_mineral_deposit_growing')


    def __init__(self,
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

        self.units_types_by_names = units_types_by_names
        self.main_base_type = main_base_type
        self.main_miner_type = main_miner_type
        self.minerals_for_main_unit_at_start = minerals_for_main_unit_at_start
        self.probability_of_mineral_deposit_growing = \
          probability_of_mineral_deposit_growing


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



_MAGIC_GAME_MAP_PHRASE = "this is scriptcraft map version 1."
_CHAR_TO_GROUND_TYPE = {'.':1, ';':2, '^':3, '_':4,
                        '@':5, ',':6, '#':7, '~':8}
_CHAR_TO_OBJECT_CONSTRUCTOR = {
    ' ':lambda: None,
    't':lambda: Tree(),
    'm':lambda: MineralDeposit(50),
}
def load_game_map(data):
    """ Return GameMap from data or raise InvalidGameMapData. """

    lines = data.split('\n')
    if not lines[0].lower().startswith(_MAGIC_GAME_MAP_PHRASE):
        raise InvalidGameMapData('Game map data must starts with %r' \
                                   % _MAGIC_GAME_MAP_PHRASE)

    del lines[0]
    # delete last line if it's blank (allow break line after last line
    # of map)
    if not lines[-1].strip():
        del lines[-1]
    rows = len(lines)
    if rows == 0:
        raise InvalidGameMapData('Game map size must be at least 1x1 '
                                 '(found 0 rows of map data).')

    columns = None
    ground_types = []
    objects = []
    start_positions = []
    for row, line in enumerate(lines):
        iter_line = iter(line)
        ground_types.append([])
        objects.append([])
        column = 0
        try:
            while True:
                try:
                    char = iter_line.next()
                except StopIteration as ex:
                    char = None

                if char in (' ', '\t', '\r', None):
                    # check number of columns
                    if columns is None:
                        if column == 0:
                            raise InvalidGameMapData( \
                              'Game map size must be at least 1x1 '
                              'found 0 fields in first row of map).')
                        columns = column
                    else:
                        if column != columns:
                            raise InvalidGameMapData( \
                              'Invalid %d row of map. Detected %d fields '
                              'but there were %d fields in first row '
                              '(make sure there is no break line '
                              'after last row of map).'
                                % (row, column, columns))
                    break

                ground_type = _CHAR_TO_GROUND_TYPE.get(char, None)
                if ground_type is None:
                    raise InvalidGameMapData( \
                      'Invalid ground type: %r of field %r' \
                      % (char, (column, row)))
                ground_types[-1].append(ground_type)

                char = iter_line.next().lower()
                if char not in ('t', 'm', ' ', 's'):
                    raise InvalidGameMapData( \
                      'Invalid object type: %r of field %r' \
                      % (char, (column, row)))
                if char != 's':
                    objects[-1].append(char)
                else:
                    start_positions.append((column, row))
                    objects[-1].append(' ')

                column += 1
        except StopIteration as ex:
            raise InvalidGameMapData('Invalid game map: unexpected '
                                     'end of line when parsing field '
                                     'at %r.' % ((column, row),))

    result = GameMap((columns, rows), start_positions)
    for x in xrange(columns):
        for y in xrange(rows):
            field = result[x, y]
            field.change_ground(ground_types[y][x])
            obj = _CHAR_TO_OBJECT_CONSTRUCTOR[objects[y][x]]()
            field.place_object(obj)
    return result


