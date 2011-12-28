#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft.core import actions, cmds, direction
from scriptcraft.core import parse
from scriptcraft.core.GameMap import FieldIsOccupied
from scriptcraft.core.Message import Message
from scriptcraft.core.Player import Player
from scriptcraft.core.Unit import Unit
from scriptcraft.core.UnitType import BEHAVIOUR_WHEN_ATTACKED
from scriptcraft.utils import *



class Game(object):

    def __init__(self, game_map, game_configuration):
        self.game_map = game_map
        self.units_by_IDs = {}
        self.players_by_IDs = {}
        self.configuration = game_configuration
        self._units_and_players_counter = 0
        self.turn_number = 0
        self.input_messages = []
        self.output_messages = []


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


    def new_player_with_base(self, name, color):
        """ May raise NoFreeStartPosition """

        player = self.new_player(name, color)

        base = self.new_unit(player, player.start_position, self.configuration.main_base_type)
        base.minerals = self.configuration.minerals_for_main_unit_at_start

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


    def _send_message(self, message):
        is_valid_ID = lambda ID: ID in self.units_by_IDs or ID == 0

        if not is_valid_ID(message.sender_ID):
            raise InvalidSender()

        if not is_valid_ID(message.receiver_ID):
            raise InvalidReceiver()

        sender = self if message.sender_ID == 0 else self.units_by_IDs[message.sender_ID]
        sender.output_messages.append(message)

        receiver = self if message.receiver_ID == 0 else self.units_by_IDs[message.receiver_ID]
        receiver.input_messages.append(message)


    def _clear_mailboxes(self):
        def clear_mailbox_of(obj):
            obj.input_messages = []
            obj.output_messages = []

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
                           'messages_len':len(unit.input_messages),
                           'x':unit.position[0],
                           'y':unit.position[1],
                           'vision_diameter':unit.type.vision_radius*2+1,
                           'extra_info': unit.minerals if unit.type.storage_size!=0 else unit.type.attack_range}
        input_data = '%(type)s %(ID)d %(player_ID)d %(messages_len)d %(x)d %(y)d %(vision_diameter)d\n%(extra_info)d\n' % input_data_dict

        # info about surroundings
        def generate_input_for_field(x, y):
            # out of map?
            is_valid_position = lambda x, y: x>=0 and y>=0 and x<self.game_map.size[0] and y<self.game_map.size[1]
            if not is_valid_position(x, y):
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

            elif field.has_unit():
                unit_ID = field.get_unit_ID()
                unit = self.units_by_IDs[unit_ID]
                unit_type = unit.type.main_name
                player_ID = unit.player.ID
                return '%s %d %d' % (unit_type, unit_ID, player_ID)

            else:
                raise Exception('invalid field')


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
                                    unit.input_messages))

        return input_data


    def find_nearest_unit_in_range_fulfilling_condition(self, position, range, condition):
        def positions_in_range(position, range):
            for x in xrange(position[0]-range,
                            position[0]+range+1):
                for y in xrange(position[1]-range,
                                position[1]+range+1):
                    if distance((x, y), position) <= range:
                        yield x, y

        the_best_distance = 99999999999
        the_nearest = None
        is_valid_position = lambda (x, y): x>=0 and y>=0 and x<self.game_map.size[0] and y<self.game_map.size[1]
        for x, y in filter(is_valid_position,
                           positions_in_range(position, range)):
            field = self.game_map[x][y]
            if field.has_unit():
                unit_ID = field.get_unit_ID()
                unit = self.units_by_IDs[unit_ID]
                dist = distance(unit.position, position)
                if dist <= the_best_distance and condition(unit):
                    the_nearest = unit
                    the_best_distance = dist

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
        pass


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
        pass


    def _generate_action_for_unit_with_fire_command(self, unit):
        pass


    def _generate_action_for_unit_with_complex_attack_command(self, unit):
        pass


    def _generate_action_for_unit_with_build_command(self, unit):
        pass


#     tic(env/folder):
#        _tic_for_world():
#            increase minerals deposit
#
#        _compile_and_run_programs():
#            for each unit
#                input = generate input for unit
#                e = CompileAndRunProgram(unit.program, input, folder=self._maybe_folder+"/env")
#                if e.maybe_compilation_status
#                    unit.last_compilation_status = maybe_compilation_status
#                unit.run_status = e.maybe_run_status
#
#        _clear_mailboxes() of all units
#
#        _analise_output():
#            for each unit
#                messages = []
#                commands = [StopCommand()]
#                if unit.running_status != NOT RUN:
#                    p = Parser(unit.running_status.output, unit.ID)
#                    messages = [create message for each stub in p.message_stubs]
#                    commands = p.commands
#
#                self._send_message(each item in messages if message is correct)
#
#                set command:
#                    unit.command = commands[-1] if not empty else StopCommand()
#                    if len(commands) != 1 then warning
#
#        _reply_system_messages()
#
#        _execute():
#            for each unit (first, copy list of units)
#                check if unit exists
#
#                # set action and execute it:
#                unit.action, errors = self._generate_action_for(unit)
#                self._execute_action_of(unit)
#
#                unit.execution_status = new ExecutionStatus(errors)
#
#
#    __init__(gamemap, configuration)
#    deepcopy()
#
#    new_player_with_base(name, color):
#        new_player()
#        add base if configuration.main_base_type != None
#        add four miners if configuration.main_miner_type != None
#
#    _generate_input_for(unit)
#    _generate_action_for(unit)
#    _execute_action_of(unit)
#    _tic_for_world
#    generate_answer_to_system_message
#    find_nearest_unit_in_range_fulfilling_condition
#    new_player(name, color)
#
#    # messages system
#    _clear_mailboxes()
#    _send_message(self, message):
#        self.messages.append(message)
#        add message to sender unit (or system)
#        add message to receiver unit (or system)
#
#    # other methods changing instance
#    new_unit(self, player, position, type)
#    remove_unit_at(self, position)
#    remove_unit(self, unit)
#
#    move_unit_at(self, unit, destination)
#    fire_at(self, destination)
#    store_minerals_from_unit_to_unit(self, source_unit, destination_unit)
#    store_minerals_from_deposit_to_unit(self, source_position, destination_unit)
#    set_minerals_to_unit(self, unit, how_many)
#    set_minerals_to_deposit(self, position_of_deposit, how_many)
#
#    set_program(unit, program)

class InvalidSender(Exception):
    pass

class InvalidReceiver(Exception):
    pass

class CannotStoreMinerals(Exception):
    pass
