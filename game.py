#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
"""

from collections import namedtuple

from tools import recordtype, Counter, exception, enum
from bash_executor import bash_executor
import texts



Field_doc = \
u"""
Klasa Field reprezentuje jednostkowy obszar na mapie gry. Posiada dwa atrybuty:
 type -- określa czym jest pole; 1 to płaski teren, 2 to wyżyny
 arg -- określa, co znajduje się *na* polu; 0 oznacza, że na polu nie znajduje
  się nic; -1 to drzewa; -2 i mniejsze liczby oznaczają złoża minerałów
  (-2 to wyeksploatowane złoża, -3 to złoża z jedną jednostką minerałów...);
  dodatnia liczba oznacza identyfikator obiektu

Zawsze używaj specjalnych funkcji do tworzenia i manipulowania polami.
Nie polegaj na atrybutach klasy Field - mogą się one zmienić. Oto lista funkcji

Konstruktor:
 new_field
 
Funkcje związane z atrybutem 'type' (czyli z tym, czym pole jest)
 is_flat
 is_upland
 
Funkcje związane z atrybutem 'arg' (czyli z tym, co znajduje się na polu)
 is_empty -- zero drzew, game_object i minerałów
 erase_object
 
 has_trees
 put_trees
 
 has_minerals_deposit
 get_minerals
 put_minerals
 
 has_game_object
 get_game_object_ID
 put_game_object
 
Funkcje kompleksowe
 is_flat_and_empty
"""
Field = namedtuple('field', ['type', 'arg'])

def new_field(uplands=False, minerals=None, object_ID=None, tree=False):
	"""
	Tworzy nowy obiekt Field. Na polu mogą się znajdować:
	 złoża minerałów (keyworded argument: minerals : int = liczba jednostek minerałów w złożu)
	 *albo* drzewa (keyworded argument: tree : bool)
	 *albo* obiekt (keyworded argument: object_ID : int)
	"""
	t = 2 if uplands else 1
	arg = 0
	if minerals != None:
		arg = -minerals-2
	if object_ID != None:
		if arg != 0:
			raise ValueError("pole moze miec zloza mineralow *albo* game_object *albo* drzewa")
		arg = object_ID
	if tree:
		if arg != 0:
			raise ValueError("pole moze miec zloza mineralow *albo* game_object *albo* drzewa")
		arg = -1
	return Field(type=t, arg=arg)
	
def is_flat(field):
	return field.type == 1
	
def is_upland(field):
	return field.type == 2

def is_flat_and_empty(field):
	return field.type == 1 and field.arg == 0
		
def is_empty(field):
	return field.arg == 0
	
def erase_object(field):
	return field._replace(arg=0)
	
def put_game_object(field, obj_ID):
	return field._replace(arg=obj_ID)

def put_trees(field):
	return field._replace(arg=-1)
	
def put_minerals(field, how_much=0):
	return field._replace(arg=-2-how_much)

def has_trees(field):
	return field.arg == -1
	
def has_minerals_deposit(field):
	return field.arg <= -2
	
def get_minerals(field):
	assert field.arg <= -2
	return -(field.arg+2)
	
def has_game_object(field):
	return field.arg > 0
	
def get_game_object_ID(field):
	return field.arg



"""
Klasy *Command reprezentują polecenia wydane jednostkom. Są to:
 StopCommand
 MoveCommand
 GatherCommand -- zbieraj minerały ze złoża lub oddaj je do obiektu
  przechowującego minerały
 FireCommand
 BuildCommand
 
Atrybuty tych klas muszą mieć odpowiedni typ, ale nie muszą być sensowne
(może być np. destination=(-2,-3); type_ID musi być poprawnym identyfikatorem
typu i direction musi przyjąć jedną z wartości DIRECTION_*).

"""
StopCommand = namedtuple('stop_command', [])
MoveCommand = namedtuple('move_command', ['direction'])
GatherCommand = namedtuple('gather_command', ['direction'])
FireCommand = namedtuple('fire_command', ['destination'])
BuildCommand = namedtuple('build_command', ['type_ID', 'direction_or_None'])



"""
Klasy *Action reprezentują czynności wykonywane przez jednostkę.

*Action nie są tym samym, co *Command. Np. obiekt może mieć komendę ruchu,
ale będzie stać, jeśli docelowe pole jest zajęte.

Reprezentanci:
 StopAction
 MoveAction
 GatherAction
 StoreAction
 FireAction
 BuildAction
 
"""
StopAction = namedtuple('stop_action', [])
MoveAction = namedtuple('move_action', ['source'])
GatherAction = namedtuple('gather_action', ['destination'])
StoreAction = namedtuple('store_action', ['storage_ID'])
FireAction = namedtuple('fire_action', ['destination'])
BuildAction = namedtuple('build_action', ['type_ID', 'destination'])



GameObject_doc = \
"""
Reprezentuje jednostkę (bazę, zbieracz lub czołg) w grze. Każda jednostka musi
należeć do jakiegoś gracza.

**Klasa abstrakcyjna!**

Atrybuty:
 ID -- unikalny identyfikator liczbowy nadawany i używany wewnętrznie przez instancję klasy Game
 player_ID -- gracz, do którego należy jednostka (zawsze określone!)
 x, y -- położenie na mapie
 command -- nadany rozkaz (np. move, stop, attack itp.)(instancja *Command)
 action -- wykonana czynność (np. move, stop)(instancja *Action)
 minerals -- zależy od rodzaju obiektu
 
"""

GameObject = recordtype('game_object', ['player_ID', 'type_ID'], {'command':StopCommand(), 'action':StopAction(), 'ID':None, 'x':None, 'y':None, 'minerals':0}, doc=GameObject_doc)
del GameObject_doc



GameObjectType_doc = \
"""
Definiuje nowy typ obiektu.

Atrybuty:
 movable -- czy obiekt potrafi się poruszać (tylko na 4 sąsiednie pola!)
 attack_range -- zasięg ataku; nie można atakować siebie; 
  0 <==> obiekt nie potrafi atakować;
 gather_size -- wielkość zbiornika na minerały; 0 <==> obiekt nie potrafi wydobywać
  złóż minerałów
 can_store_minerals -- czy obiekt potrafi przechowywać minerały?
 can_build -- czy obiekt potrafi budować?
 cost_of_build -- koszt budowy obiektu; -1 <==> obiektu nie można budować
 when_attacked_get_minerals -- wymaga can_store_minerals==True;
  jeżeli False, to zaatakowany obiekt jest niszczony (z pewnym prawdopodobieństwem);
  jeżeli True, to zaatakowany obiekt traci minerały i jest niszczony na 100% dopiero
  wtedy, gdy zabraknie mu minerałów
 
** Obecna implementacja wyklucza (gather_size != 0 and can_store_minerals) ** 
"""
d = {
	'movable' : True,
	'attack_range' : 0,
	'gather_size' : 0,
	'can_store_minerals' : False,
	'can_build' : False,
	'cost_of_build' : -1,
	'when_attacked_get_minerals' : False,
}
GameObjectType = recordtype('game_object_type', ['name', 'constructor', 'ID'], d, doc=GameObjectType_doc)
del GameObjectType_doc, d
OBJECT_TYPE_NAME_TO_TYPE_ID = {'TANK':'t', 'T':'t', 'MINER':'m', 'M':'m', 'BASE':'b', 'B':'b'}

BASE_TYPE_ID = 'b'
MINER_TYPE_ID = 'm'
TANK_TYPE_ID = 't'
BASE_TYPE = GameObjectType(ID=BASE_TYPE_ID, name='base', movable=False, can_build=True, when_attacked_get_minerals=True, can_store_minerals=True,
						 	constructor=lambda player_ID: GameObject(type_ID='b', player_ID=player_ID))
MINER_TYPE = GameObjectType(ID=MINER_TYPE_ID, name='miner', gather_size=1, cost_of_build=3,
						 	constructor=lambda player_ID: GameObject(type_ID='m', player_ID=player_ID, minerals=0))
TANK_TYPE = GameObjectType(ID=BASE_TYPE_ID, name='tank', attack_range=3, cost_of_build=10,
						 	constructor=lambda player_ID: GameObject(type_ID='t', player_ID=player_ID))
					
GAME_OBJECT_TYPES_BY_ID = {
	TANK_TYPE_ID : TANK_TYPE,
	MINER_TYPE_ID : MINER_TYPE,
	BASE_TYPE_ID : BASE_TYPE,
}




Language_doc = \
"""
Reprezentuje język programowania.

Atrybuty:
 ID -- unikalny identyfikator
 name -- pełna nazwa (np. 'Python 2.7.2')
 compilation_command -- polecenie konsoli służące do kompilacji
 run_command -- polecenie konsoli służące do uruchomienia
 source_file_name -- nazwa, jaką powinnien mieć plik źródłowy
 binary_file_name -- nazwa, jaką będzie mieć binarka
 
* compilation_command i run_command powinny być poleceniami, które zadziałają
zarówno na Windowsie, jak i Linuksie! *

"""

Language = recordtype('language', ['ID', 'name', 'compilation_command', 'run_command', 'source_file_name', 'binary_file_name'], doc=Language_doc)
del Language_doc

NO_LANGUAGE_ID = ''
NO_LANGUAGE = Language(
	ID = NO_LANGUAGE_ID,
	name = '',
	compilation_command = '',
	run_command = '',
	source_file_name = 'file',
	binary_file_name = 'file',
)
CPP_LANGUAGE_ID = 'cpp'
CPP_LANGUAGE = Language(
	ID = CPP_LANGUAGE_ID,
	name = 'c++',
	compilation_command = 'gcc input.cpp -o output.exe',
	run_command = './output.exe',
	source_file_name = 'input.cpp',
	binary_file_name = 'output.exe',
)
PYTHON_LANGUAGE_ID = 'py'
PYTHON_LANGUAGE = Language(
	ID = PYTHON_LANGUAGE_ID,
	name = 'python',
	compilation_command = 'python -c "import py_compile; py_compile.compile(\'file.py\')"',
	run_command = 'python file.pyc',
	source_file_name = 'file.py',
	binary_file_name = 'file.pyc',
)
LANGUAGES_BY_ID = {
	NO_LANGUAGE_ID : NO_LANGUAGE,
	CPP_LANGUAGE_ID : CPP_LANGUAGE,
	PYTHON_LANGUAGE_ID : PYTHON_LANGUAGE,
}
	


ProgramExecution_doc = \
"""
Mutowalny rekord reprezentujący informacje o wykonania i prasowaniu wyjścia
programu gracza.

Atrybuty
 compilation_errors -- wyjście kompilatora
 is_compilation_successful -- czy kompilacja zakończyła się powodzeniem?
 is_run_successful -- czy program został uruchomiony i zakończył działanie bez błędów?
 input -- wejście na program
 output -- wyjście wygenerowane przez program
 errors_output -- wyjście strumienia błędów
 parse_errors -- komunikaty błędów, jakie wystąpiły podczas parsowania wyjścia programu
 executing_command_errors -- komunikaty błędów, jakie wystąpiły podczas wykonywania komend
 
"""

ProgramExecution = recordtype('program_execution', ['compilation_errors', 'is_compilation_successful'],
	{'input':'', 'output':'', 'error_output':'', 'is_run_successful':False, 'parse_errors':'', 'executing_command_errors':''},
	doc=ProgramExecution_doc
)
del ProgramExecution_doc



Player_doc = \
"""
Reprezentuje gracza w grze.

Atrybuty
 ID -- unikalny identyfikator liczbowy nadawany i używany wewnętrznie przez instancję klasy Game
 name -- nazwa gracza (nie musi być unikalna)
 program_code -- kod programu gracza
 language_ID -- identyfikator języka, w którym jest napisany program
 program_execution -- instancja klasy ProgramExecution, używane przez instancję klasy Game
 
"""

Player = recordtype('player', ['name', 'program_code', 'language_ID'], {'ID':None, 'program_execution':None, 'base_ID':None, 'object_IDs':[]}, doc=Player_doc)
del Player_doc



""" kierunki świata """
DIRECTION_N, DIRECTION_E, DIRECTION_S, DIRECTION_W = 'n', 'e', 's', 'w'
DIRECTION_TO_RAY = {DIRECTION_N:(0,-1), DIRECTION_E:(1,0), DIRECTION_S:(0,1), DIRECTION_W:(-1,0)}
DIRECTIONS = {'N':DIRECTION_N, 'E':DIRECTION_E, 'S':DIRECTION_S, 'W':DIRECTION_W}



""" Exceptions """
NotEmptyFieldException = exception('NotEmptyFieldException')
NoFreeStartPositions = exception('NoFreeStartPositions')
ParseError = exception('ParseError')
ExecutingCommandError = exception('ExecutingCommandError')



""" Funkcje """
def distance_between(p1, p2):
	""" Zwraca odległość między p1=(x1,y1) a p2=(x2,y2) w metryce miejskiej. """
	return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])
		
		

""" Klasy """
class GameMap (list):

	def __init__(self, size, start_positions=[]):
		"""
		Tworzy kwadratową, pustą, płaską mapę.

		Arguments:
		size -- długość boku mapy
		start_positions -- lista pozycji startowych (x,y);
		 metoda reserve_next_free_start_position może zwracać pozycje startowe
		 w innej kolejności!
		 
		* Pozycje startowe nie mogą znajdować się na skraju mapy! *
		
	    """

		assert all(map(lambda (x,y): 0<x<size-1 and 0<y<size-1, start_positions)) # check start positions

		super(GameMap, self).__init__(  [[new_field() for y in xrange(size)] for x in xrange(size)]  )
		self._free_start_positions = start_positions
		self.size = size
		
	def reserve_next_free_start_position(self):
		"""
		Nigdy nie zwraca dwa razy tej samej pozycji startowej.
		
		Jako wolną pozycję startową traktuje się taką pozycję, że ta pozycja oraz
		cztery sąsiadujące do niej pola są puste i płaskie.
		
		Może rzucić NoFreeStartPositions.
		
		"""
		
		for i in self._free_start_positions:
			x, y = i
			fields = (self[x][y], self[x][y-1], self[x][y+1], self[x+1][y], self[x-1][y])
			if all(map(is_flat_and_empty, fields)): # if all fields are flat and empty
				self._free_start_positions.remove(i)
				return i
		raise NoFreeStartPositions()
		
	def is_valid_position(self, x, y):
		"""
		Sprawdza, czy podane współrzędne mieszczą się w granicach mapy. Pomaga
		zapobiegać IndexErrorom.
		
		"""
		
		return x>=0 and y>=0 and x<self.size and y<self.size
	
	def find_path_from_to(self, source, dest):
		""" Zwraca kierunek, w którym należy pójsć od source """
	
		return NotImplemented
	
	def __str__(self):
		""" Wielowierszowa reprezentacja mapy """
	
		s = "Map (size=%d)\n" % self.size
		for y in xrange(self.size):
			for x in xrange(self.size):
				field = self[x][y]
				if has_trees(field):
					s += 'trees'.center(7)
				elif has_minerals_deposit(field):
					s += ('m %d m' % get_minerals(field)).center(7)
				elif has_game_object(field):
					s += ('<%d>' % get_game_object_ID(field)).center(7)
				else:
					s += '.'.center(7)
				s += " "
			s += "\n"
		return s
				
	    	    

class Game (object):

	def __init__(self, game_map, players=[]):
		"""
		Argumenty:
		 game_map -- instancja klasy GameMap;
		 players -- lista instancji klasy Player z zainicjowanymi atrybutami
		  name i program_code

		"""
		
		assert isinstance(game_map, GameMap)
		assert isinstance(players, list)
		
		self.minerals_for_base_at_start = 50

		self._bash_executor = bash_executor
		self._map = game_map
		self._objects_by_ID = {}
		self._players_by_ID = {}
		self._objects_counter = Counter(1)		
		self._players_counter = Counter(1)	
		
		map(self.add_player, players)
			
	def add_player(self, player):
		"""
		Dodaje nowego gracza, bazę z minerałami na wolnej pozycji startowej
		oraz 4 minery dookoła bazy.
		
		player powinien mieć prawidłowo ustawione program_code i language_ID!
		
		Może rzucić NoFreeStartPositions.
		
		"""
	
		assert isinstance(player, Player)
		assert player.language_ID in LANGUAGES_BY_ID
	
		x, y = self._map.reserve_next_free_start_position() # może rzucić NoFreeStartPositions
	
		# add player
		player.ID = self._players_counter()
		self._players_by_ID[player.ID] = player

		# add base
		base = BASE_TYPE.constructor(player.ID)
		self._add_game_object(base, x, y)
		base.minerals = self.minerals_for_base_at_start
		player.base_ID = base.ID
		
		# add miners
		miner = MINER_TYPE.constructor(player.ID)
		self._add_game_object(miner, x+1, y)
		self._add_game_object(miner.copy(), x-1, y)
		self._add_game_object(miner.copy(), x, y+1)
		self._add_game_object(miner.copy(), x, y-1)						
		
	def set_program(self, player_ID, program_code, language_ID):
		assert language_ID in LANGUAGES_BY_ID
		assert player_ID in self._players_by_ID
		assert isinstance(program_code, str)
		
		player = self._players_by_ID[player_ID]
		player.program_code = program_code
		player.language_ID = language_ID
		
	def tic(self):
		self._compile_and_run_programs()
		self._parse_programs_outputs()
		self._run_commands()
		
	def _compile_and_run_programs(self):
		for player_ID, player in self._players_by_ID.items():
			# compilation
			s = open('cache/plik', 'w'); s.write(player.program_code); s.close()
			language = LANGUAGES_BY_ID[player.language_ID]
			_, errors_output, exit_code = self._bash_executor(language.compilation_command, 
				{'cache/plik':language.source_file_name},
				{language.binary_file_name:'cache/binary'}
			)
			compilation_successful = exit_code == 0
			player.program_execution = ProgramExecution(compilation_errors=errors_output, is_compilation_successful=compilation_successful)
			
			# prepare input for running
			input_data = ''
			player.program_execution.input = input_data
			
			# run!
			if player.program_execution.is_compilation_successful:
				output, errors_output, exit_code = self._bash_executor(language.run_command, 
					{'cache/binary':language.binary_file_name},
					input_data=input_data,
				)
				player.program_execution.output = output
				player.program_execution.errors_output = errors_output
				player.program_execution.is_run_successful = exit_code == 0
			else:
				player.program_execution.output = ''
				player.program_execution.errors_output = ''
				player.program_execution.is_run_successful = False

	def _parse_programs_outputs(self):
		def parse_as_int(data):
			""" W przypadku niepowodzenia zwraca None """

			if len(data)>8:
				return None
			try:
				return int(data)
			except ValueError:
				return None
	
		def parse_as_direction(data):
			""" W przypadku niepowodzenia zwraca None """

			try:
				return DIRECTIONS[data.upper()]
			except KeyError:
				return None

		def parse_as_str(data, max_string_length=256):
			""" W przypadku, gdy długość stringa przekracza max_string_length,
			zwraca None """
	
			if len(data) > max_string_length:
				return None
			return data	


		for game_object in self._objects_by_ID.values():
			game_object.command = None
			
		for player_ID, player in self._players_by_ID.items():
			output = player.program_execution.output
			player.program_execution.parse_errors = ''
			
			for line_no, line in enumerate(output.split('\n')):
				errors_info = {'line_no':line_no+1, 'line':line, 'invalid_part':line}			
				
				try:
					# parse command
					splited_line = line.split()
					if len(splited_line) == 0: # empty line
						continue
					command_as_string = splited_line[0].lower()

					# parse object ID
					if len(splited_line) <= 1:
						raise ParseError(texts.parse_errors['no_game_object_ID'] % errors_info)
					object_ID = parse_as_int(splited_line[1])
					if object_ID == None:
						raise ParseError(texts.parse_errors['parsing_game_object_ID_error'] % errors_info)
					
					# parse arguments of command
					args_of_command = splited_line[2:]			
					
					if command_as_string in ('stop', 's'):
						command = StopCommand()				

					elif command_as_string in ('move', 'm'):
						if len(args_of_command) != 1:
							raise ParseError(texts.parse_errors['invalid_move_command_args'] % errors_info)				
							
						direction = parse_as_direction(args_of_command[0])
						if direction == None:
							errors_info['invalid_part'] = args_of_command[0]
							raise ParseError(texts.parse_errors['parsing_direction_error'] % errors_info)

						command = MoveCommand(direction=direction)
					
					elif command_as_string in ('gather', 'g'):
						if len(args_of_command) != 1:
							raise ParseError(texts.parse_errors['invalid_gather_command_args'] % errors_info)

						direction = parse_as_direction(args_of_command[0])
						if direction == None:
							errors_info['invalid_part'] = args_of_command[0]
							raise ParseError(texts.parse_errors['parsing_direction_error'] % errors_info)

						command = GatherCommand(direction=direction)
					
					elif command_as_string in ('fire', 'f'):
						if len(args_of_command) != 2:
							raise ParseError(texts.parse_errors['invalid_fire_command_args'] % errors_info)			

						dest_x, dest_y = parse_as_int(args_of_command[0]), parse_as_int(args_of_command[1])
						if dest_x == None or dest_y == None:
							errors_info['invalid_part'] = args_of_command[0] if dest_x == None else args_of_command[1]
							raise ParseError(texts.parse_errors['invalid_fire_command_args'] % errors_info)

						command = FireCommand(destination=(dest_x,dest_y))

					elif command_as_string in ('build', 'b'):
						if len(args_of_command) not in (1, 2):
							raise ParseError(texts.parse_errors['invalid_build_command_args'] % errors_info)				

						type_name = parse_as_str(args_of_command[0])
						if type_name == None:
							errors_info['invalid_part'] = args_of_command[0]
							raise ParseError(texts.parse_errors['invalid_build_command_args'] % errors_info)
						type_ID = OBJECT_TYPE_NAME_TO_TYPE_ID.get(type_name.upper(), None)
						if type_ID == None:
							raise ParseError(texts.parse_errors['invalid_object_type'] % errors_info)
						
						direction = None
						if len(args_of_command) == 2:
							errors_info['invalid_part'] = args_of_command[1]
							direction = parse_as_direction(args_of_command[1])
							if direction == None:
								raise ParseError(texts.parse_errors['invalid_object_type'] % errors_info)
				
						command = BuildCommand(type_ID=type_ID, direction_or_None=direction)
					
					else: # unknown command
						errors_info['invalid_part'] = command_as_string
						raise ParseError(texts.parse_errors['unknown_command'] % errors_info)
					
					# we are here only if there is no errors
					game_object = self._objects_by_ID.get(object_ID, None)
					if game_object == None:
						errors_info['invalid_part'] = splited_line[1]
						raise ParseError(texts.parse_errors['invalid_game_object_ID'] % errors_info)
					else:
						if game_object.command != None:
							player.program_execution.parse_errors += texts.warnings['changing_command_of_game_object'] % {'line_no':line_no, 'line':line, 'object_ID':game_object.ID}
						game_object.command = command					
					
				except ParseException as ex:
					player.program_execution.parse_errors += ex.args[0]
		
		# set default commands
		for obj in self._objects_by_ID.values():
			if obj.command == None:
				player = self._players_by_ID[obj.player_ID]
				player.program_execution.parse_errors += texts.warnings['no_command_for_object'] % {'object_ID':obj.ID}
				obj.command = StopCommand()
		
	def _run_commands(self):
		for player in self._players_by_ID.values():
			player.program_execution.executing_command_errors = ''
	
		objects_by_ID = self._objects_by_ID.copy()
		for object_ID in objects_by_ID:
			obj = self._objects_by_ID.get(object_ID, None)
			if obj == None: # jednostka mogła już zostać zniszczona przez atak innej jednostki; usunięcie jednostki z self._objects_by_ID nie ma wpływu na objects_by_ID
				continue
			command = obj.command
			obj.action = StopAction()
			
			try:
				if isinstance(command, StopCommand):
					pass
				
				elif isinstance(command, MoveCommand):
					direction = command.direction
					delta_x, delta_y = DIRECTION_TO_RAY[direction]
					dest_x, dest_y = obj.x + delta_x, obj.y + delta_y
					self._try_move_object(obj, dest_x, dest_y)
				
				elif isinstance(command, GatherCommand):
					direction = command.direction
					delta_x, delta_y = DIRECTION_TO_RAY[direction]
					dest_x, dest_y = obj.x + delta_x, obj.y + delta_y
					self._try_gather(obj, dest_x, dest_y)
				
				elif isinstance(command, FireCommand):
					dest_x, dest_y = command.destination
					self._try_attack(obj, dest_x, dest_y)
				
				elif isinstance(command, BuildCommand):
					type_ID, direction_or_None = command.type_ID, command.direction_or_None
					object_type = GAME_OBJECT_TYPES_BY_ID[type_ID]
					dest_x, dest_y = obj.x, obj.y
					if direction_or_None == None:
						destinations = [(dest_x, dest_y-1), (dest_x+1, dest_y), (dest_x, dest_y+1), (dest_x-1, dest_y)]
					else:
						delta_x, delta_y = DIRECTION_TO_RAY[direction_or_None]
						destinations = [(dest_x+delta_x, dest_y+delta_y)]
					self._try_build(obj, object_type, destinations)
			
			except ExecutingCommandError as ex:
				player = self._players_by_ID[obj.player_ID]
				player.program_execution.executing_command_errors += ex.args[0]

	def _try_move_object(self, obj, dest_x, dest_y):
		"""
		Próbuje przemieścić obiekt obj w miejsce (dest_x, dest_y).
		
		dest_x, dest_y mogą być niepoprawnymi koordynatami (np. -2, -3);
		
		Jeśli docelowe miejsce jest zajęte, nie przemieszcza obiektu.
		
		Jeśli obiekt nie posiada umiejętności poruszania się, obiekt nie zostaje
		przemieszony.
		
		Jeśli przemieszczenie *nie* zakończyło się sukcesem, rzuca ExecutingCommandError.
				
		"""
		
		errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
		object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
		if not object_type.movable:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_move_object_not_movable'] % errors_info)
		if not self._map.is_valid_position(dest_x, dest_y):
			raise ExecutingCommandError(texts.executing_command_errors['cannot_move_invalid_map_position'] % errors_info)
		dest_field = self._map[dest_x][dest_y]
		if not is_empty(dest_field):
			raise ExecutingCommandError(texts.executing_command_errors['cannot_move_field_not_empty'] % errors_info)
		
		self._map[obj.x][obj.y] = erase_object(self._map[obj.x][obj.y])
		obj.x, obj.y = dest_x, dest_y
		self._map[dest_x][dest_y] = put_game_object(dest_field, obj.ID)
		
	def _try_gather(self, obj, dest_x, dest_y):
		""" Patrz self._try_move """

		errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
		object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
		if object_type.gather_size == 0:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_object_cannot_gather'] % errors_info)
		if not self._map.is_valid_position(dest_x, dest_y):
			raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_invalid_map_position'] % errors_info)
		field = self._map[dest_x][dest_y]
		
		if not has_minerals_deposit(field):
			if not has_game_object(field):
				raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_no_minerals_deposit_neither_object'] % errors_info)
			dest_object_ID = get_game_object_ID(field)
			dest_obj = self._objects_by_ID[dest_object_ID]
			dest_obj_type = GAME_OBJECT_TYPES_BY_ID[dest_obj.type_ID]
			if not dest_obj_type.can_store_minerals:
				raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_destination_object_cannot_store_minerals'] % errors_info)
				
			dest_obj.minerals += obj.minerals
			obj.minerals = 0
		else:
			how_much_minerals_can_get_obj = object_type.gather_size-obj.minerals
			if how_much_minerals_can_get_obj == 0:
				raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_object_is_full'] % errors_info)
			how_much_minerals_in_deposit = get_minerals(field)
			if how_much_minerals_in_deposit == 0:
				raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_mineral_deposit_is_empty'] % errors_info)
			
			how_much_minerals = min(how_much_minerals_can_get_obj, how_much_minerals_in_deposit)
			obj.minerals += how_much_minerals
			self._map[dest_x][dest_y] = put_minerals(field, how_much_minerals_in_deposit-how_much_minerals)
		
	def _try_attack(self, obj, dest_x, dest_y):
		""" Patrz self._try_move """

		errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
		object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
		if object_type.attack_range == 0:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_object_cannot_attack'] % errors_info)
		if not self._map.is_valid_position(dest_x, dest_y):
			raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_invalid_map_position'] % errors_info)
		distance = distance_between((obj.x,obj.y),(dest_x,dest_y))
		if object_type.attack_range < distance:
			errors_info['distance'], errors_info['attack_range'] = distance, attack_range
			raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_destination_too_far'] % errors_info)
		if distance == 0:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_itself'] % errors_info)
		
		self._attack(dest_x, dest_y)
		
	def _attack(self, dest_x, dest_y):
		field = self._map[dest_x][dest_y]
		if has_trees(field):
			self._map[dest_x][dest_y] = erase_object(field)
		elif has_game_object(field):
			obj = self._objects_by_ID[get_game_object_ID(field)]
			if GAME_OBJECT_TYPES_BY_ID[obj.type_ID].when_attacked_get_minerals and obj.minerals > 0:
				obj.minerals -= 1
			else:
				self._remove_game_object_at(dest_x, dest_y)
			
	def _try_build(self, builder_object, built_object_type, destinations):
		""" Patrz self._try_move """

		errors_info = {'object_ID':builder_object.ID, 'built_object_name':built_object_type.name}		
		builder_object_type = GAME_OBJECT_TYPES_BY_ID[builder_object.type_ID]
		if not builder_object_type.can_build:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_build_object_cannot_build'] % errors_info)
		if built_object_type.cost_of_build == -1:
			raise ExecutingCommandError(texts.executing_command_errors['cannot_build_built_object_cannot_be_built'] % errors_info)
		if builder_object.minerals < built_object_type.cost_of_build:
			errors_info['minerals_in_builder'] = builder_object.minerals
			errors_info['required_minerals'] = built_object_type.cost_of_build
			raise ExecutingCommandError(texts.executing_command_errors['cannot_build_too_few_minerals'] % errors_info)
		for dest_x, dest_y in destinations:
			if self._map.is_valid_position(dest_x, dest_y):
				field = self._map[dest_x][dest_y]
				if is_flat_and_empty(field):
					built_object = built_object_type.constructor(builder_object.player_ID)
					builder_object.minerals -= built_object_type.cost_of_build
					self._add_game_object(built_object, dest_x, dest_y)
		raise ExecutingCommandError(texts.executing_command_errors['cannot_build_no_free_space'] % errors_info)
		
	def _add_game_object(self, game_object, x, y):
		""" Może rzucić NotEmptyFieldException """
		
		if not is_empty(self._map[x][y]):
			raise NotEmptyFieldException('Field (%d, %d) is not empty' % (x,y))
		game_object.ID = self._objects_counter()
		game_object.x, game_object.y = x, y
		player = self._players_by_ID[game_object.player_ID]
		player.object_IDs.append(game_object.ID)
		self._objects_by_ID[game_object.ID] = game_object
		self._map[x][y] = put_game_object(self._map[x][y], game_object.ID)
		
	def _remove_game_object_at(self, x, y):
		field = self._map[x][y]
		object_ID = get_game_object_ID(field)
		obj = self._objects_by_ID[object_ID]
		self._map[x][y] = erase_object(field)
		del self._objects_by_ID[object_ID]		

		player = self._players_by_ID[obj.player_ID]
		player.object_IDs.remove(object_ID)
		if player.base_ID == object_ID:
			player.base_ID = None		
		
		
tprogram_code = """
print "BUILD 1 T"
print "MOVE 2 E"
"""
tgame = Game(game_map=GameMap(size=8, start_positions=[(2,2),(4,2),(6,2)]), players=[Player(name='blb',program_code=tprogram_code, language_ID=PYTHON_LANGUAGE_ID)])
def t():
	tgame.tic()
	print "Objects:"
	for k,v in tgame._objects_by_ID.items():
		print "%d -> %s" % (k, v)
	print "Players:"
	for k,v in tgame._players_by_ID.items():
		print "  player %d -> object_IDs = %s" % (k, v.object_IDs)
		print "\n".join(map(lambda x: ' '*4+x, v.program_execution.parse_errors.split('\n')))
		print "\n".join(map(lambda x: ' '*4+x, v.program_execution.executing_command_errors.split('\n')))
		print "\n".join(map(lambda x: ' '*4+x, v.program_execution.output.split('\n')))
	print tgame._map
		
def c():
	l = 0
	import time
	while True:
		print "Tura %d" % l
		l += 1
		t()
		time.sleep(0.5)

