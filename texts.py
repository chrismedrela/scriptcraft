#!/usr/bin/env python
#-*- coding:utf-8 -*-

_error_prefix = 'BŁĄD (wiersz %(line_no)5d) : '
_error_sufix = '\n'
parse_errors = {
	'unknown_command' : 'nieznane polecenie "%(command)s"',
	'wrong_number_of_arguments' : 'nieprawidłowa liczba argumentów (%(number_of_args)d) dla polecenia "%(command)s"',
	'invalid_argument' : 'nieprawidłowy %(invalid_arg_no)d. argument "%(invalid_arg)s" polecenia "%(command)s"',
	'invalid_object_ID' : 'nie istnieje obiekt o ID=%(object_ID)d',
	'no_base' : 'nie masz już bazy - nie możesz budować',
	'object_not_belong_to_player' : 'nie możesz sterować obiektem o ID=%(object_ID)d, ponieważ należy on do przeciwnika',
}
for k in parse_errors:
	parse_errors[k] = _error_prefix + parse_errors[k] + _error_sufix


_warning_prefix_with_line_no = 'WARN (wiersz %(line_no)5d) : '
_warning_prefix_with_object_ID = 'WARN (obiekt %(object_ID)5d) : '
_warning_sufix = '\n'
warnings = {
	'changing_command_of_game_object' : _warning_prefix_with_line_no+'obiektowi ID=%(object_ID)d nadano już wcześniej komendę'+_warning_sufix,
	'no_command_for_object' : _warning_prefix_with_object_ID+'nie nadano komendy obiektowi ID=%(object_ID)d'+_warning_sufix,
}


_executing_command_error_prefix = 'BŁĄD (obiekt %(object_ID)5d) : '
_executing_command_error_sufix = '\n'
executing_command_errors = {
	'cannot_move_invalid_map_position' : 'obiekt nie może się ruszyć - ruch poza mapę (%(x)d, %(y)d) niedozwolony',
	'cannot_move_field_not_empty' : 'obiekt nie może się ruszyć - docelowe pole (%(x)d, %(y)d) jest już zajęte',
	'cannot_move_object_not_movable' : 'obiekt nie może się ruszyć - nie ma takiej umiejętności',
	'cannot_gather_invalid_map_position' : 'obiekt nie może zbierać minerałów - zbieranie minerałów spoza mapy (%(x)d, %(y)d) niedozwolone',
	'cannot_gather_no_minerals_deposit_neither_object' : 'obiekt nie może zbierać ani oddać minerałów - brak złóż minerałów ani obiektu przechowującego minerały w (%(x)d, %(y)d)',
	'cannot_gather_destination_object_cannot_store_minerals' : 'obiekt nie może oddać minerałów - docelowy obiekt nie ma umiejętności przechowywania minerałów',
	'cannot_gather_object_cannot_gather' : 'obiekt nie może zbierać minerałów - nie ma takiej umiejętności',
	'cannot_gather_object_is_full' : 'obiekt nie może zbierać minerałów - jego zbiornik minerałów jest już pełny',
	'cannot_gather_mineral_deposit_is_empty' : 'obiekt nie może zbierać minerałów - złoża w (%(x)d, %(y)d) są już wyczerpane',
	'cannot_attack_invalid_map_position' : 'obiekt nie może atakować - atak miejsc znajdujących się poza mapą (%(x)d, %(y)d) niedozwolony',
	'cannot_attack_object_cannot_attack' : 'obiekt nie może atakować - nie ma takiej umiejętności',
	'cannot_attack_destination_too_far' : 'obiekt nie może atakować - miejsce ataku (%(x)d, %(y)d) leży za daleko (%(distance)d odległości, zasięg ataku to jedynie %(attack_range)d)',
	'cannot_attack_itself' : 'obiekt nie może atakować - nie można zaatakować siebie',
	'cannot_build_object_cannot_build' : 'obiekt nie może budować - nie ma takiej umiejętności',
	'cannot_build_built_object_cannot_be_built' : 'obiekt nie może budować - nie można budować jednostek "%(built_object_name)s"',
	'cannot_build_too_few_minerals' : 'obiekt nie może budować - za mało minerałów (potrzeba %(required_minerals)d jednostek, obiekt budujący ma tylko %(minerals_in_builder)d jednostek)',
	'cannot_build_no_free_space' : 'obiekt nie może budować - brak wolnego miejsca dla nowej jednostki typu "%(built_object_name)s"',
}

for k in executing_command_errors:
	executing_command_errors[k] = _executing_command_error_prefix + executing_command_errors[k] + _executing_command_error_sufix

