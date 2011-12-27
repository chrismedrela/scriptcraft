#!/usr/bin/env python
#-*- coding:utf-8 -*-

from scriptcraft.core import direction
from scriptcraft.core.GameMap import FieldIsOccupied
from scriptcraft.core.Player import Player
from scriptcraft.core.Unit import Unit
from scriptcraft.core.UnitType import BEHAVIOUR_WHEN_ATTACKED



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

        if destination.minerals == destination.type.store_size:
            raise CannotStoreMinerals('destination unit is full')

        minerals_in_source = field_with_source.get_minerals()
        self.game_map.erase_at(source_position)
        self.game_map.place_minerals_at(source_position, minerals_in_source-1)

        destination.minerals += 1


    def store_minerals_from_unit_to_unit(self, source, destination):
        if source.minerals == 0:
            raise CannotStoreMinerals('source unit is empty')

        if destination.minerals == destination.type.store_size:
            raise CannotStoreMinerals('destination unit is full')

        source.minerals -= 1
        destination.minerals += 1










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

class InvalidReceiver(Exception):
    pass

class CannotStoreMinerals(Exception):
    pass
