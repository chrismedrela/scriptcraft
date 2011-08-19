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
	'compilation_done_in_another_session' : 'brak informacji - kompilacja programu nastąpiła podczas innej sesji',
}


_executing_command_error_prefix = 'BŁĄD (obiekt %(object_ID)5d) : '
_executing_command_error_sufix = '\n'
executing_command_errors = {
	'object_not_movable' : 'nie można wykonać polecenia, bo obiekt nie ma umiejętności poruszania się',
	'invalid_position' : 'nie można wykonać polecenia, bo koordynaty leżą poza granicami mapy',
	'no_path' : 'nie znaleziono ścieżki',
	'cannot_move_field_not_empty' : 'nie można się przemieścić na zajęte pole',
	'object_cannot_gather' : 'ten obiekt nie potrafi wydobywać złóż minerałów',
	'cannot_gather_no_minerals_deposit_neither_base' : 'nie można wykonać polecenia GATHER - we wskazanym miejscu nie ma złóż minerałów ani bazy',
	'cannot_gather_destination_object_cannot_store_minerals' : 'nie można magazynować minerałów w obiektach innych niż baza',
	'cannot_gather_object_is_full' : 'nie można już zebrać więcej minerałów - zbiornik na minerały już pełny',
	'cannot_gather_mineral_deposit_is_empty' : 'to złoże jest wyeksploatowane',
	'no_base_no_gather' : 'nie masz bazy => nie masz gdzie magazynować minerałków!',
	'object_cannot_attack' : 'ta jednostka nie potrafi atakować',
	'cannot_attack_destination_too_far' : 'obiekt nie może atakować - miejsce ataku (%(x)d, %(y)d) leży za daleko (%(distance)d odległości, zasięg ataku to jedynie %(attack_range)d)',
	'cannot_attack_itself' : 'nie można zaatakować siebie',
	'attacking_your_objects_stopped' : 'na polu do zaatakowania znajduje się Twoja jednostka - atak wstrzymano',
	'cannot_build_object_cannot_build' : 'obiekt nie może budować - nie ma takiej umiejętności',
	'cannot_build_built_object_cannot_be_built' : 'obiekt nie może budować - nie można budować jednostek "%(built_object_name)s"',
	'cannot_build_too_few_minerals' : 'obiekt nie może budować - za mało minerałów (potrzeba %(required_minerals)d jednostek, obiekt budujący ma tylko %(minerals_in_builder)d jednostek)',
	'cannot_build_no_free_space' : 'obiekt nie może budować - brak wolnego miejsca dla nowej jednostki typu "%(built_object_name)s"',
	'cannot_complex_gather_destination_has_no_deposit' : 'w docelowym polu nie ma złóż minerałów',
	'build_warning_unknown_object_ID' : 'nieprawidłowy ID obiektu, od którego ma być skopiowany program - mimo to jednostkę zbudowano'
}

for k in executing_command_errors:
	executing_command_errors[k] = _executing_command_error_prefix + executing_command_errors[k] + _executing_command_error_sufix

