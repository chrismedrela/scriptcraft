#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
"""

from collections import namedtuple
import hashlib
import os
import random

import aima.search

from tools import recordtype, Counter, exception, enum
from bash_executor import bash_executor
import texts



Field_doc = \
u"""
Klasa Field reprezentuje jednostkowy obszar na mapie gry. Posiada dwa atrybuty:
 type -- określa czym jest pole; 1 to płaski teren, 2 to wyżyny
 arg -- określa, co znajduje się *na* polu; 0 oznacza, że na polu nie znajduje
  się nic; -1 to drzewa; -2 i mniejsze liczby oznaczają złoża minerałów
  (-2 to wyeksploatowane złoża, -3 to złoża z jedną jednostką minerałów...,
  -4 to złoża z dwoma jednostkami...);
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



Message_doc = \
"""
sender_ID i receiver_ID mogą być równe zero; wtedy oznacza to, że nadawcą/odbiorcą
jest system gry.

"""

Message = namedtuple('message', ['sender_ID', 'receiver_ID', 'text'])




Program_doc = \
"""
Reprezentuje program. Składa się z opcjonalnych atrybutów 'code' i 'language_ID'.
W przypadku nie podania ich, domyślne wartości to odpowiednio '' i NO_LANGUAGE_ID

"""

Program = recordtype('program', [], {'code':'', 'language_ID':NO_LANGUAGE_ID}, doc=Program_doc)
del Program_doc



"""
Klasy *Command reprezentują polecenia wydane jednostkom. Są to:
 StopCommand
 MoveCommand
 GatherCommand -- zbieraj minerały ze złoża lub oddaj je do obiektu
  przechowującego minerały
 FireCommand
 BuildCommand -- program_object_ID_or_zero to ID obiektu, którego program ma być
  użyty dla nowo budowanej jednostki
 
Atrybuty tych klas muszą mieć odpowiedni typ, ale nie muszą być sensowne
(może być np. destination=(-2,-3); type_ID musi być poprawnym identyfikatorem
typu i direction musi przyjąć jedną z wartości DIRECTION_*).

"""
StopCommand = namedtuple('stop_command', [])
MoveCommand = namedtuple('move_command', ['direction'])
ComplexMoveCommand = namedtuple('complex_move_command', ['destination'])
GatherCommand = namedtuple('gather_command', ['direction'])
ComplexGatherCommand = namedtuple('complex_gather_command', ['destination'])
FireCommand = namedtuple('fire_command', ['destination'])
ComplexAttackCommand = namedtuple('complex_attack_command', ['destination'])
BuildCommand = namedtuple('build_command', ['type_ID', 'direction_or_None', 'program_object_ID_or_zero'])



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

GameObject = recordtype('game_object', ['player_ID', 'type_ID',],
	{'program_execution':None, 'program':Program(), 'command':StopCommand(),
		'action':StopAction(), 'messages':[], 'ID':None, 'x':None, 'y':None, 'minerals':0
	}, doc=GameObject_doc)
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
 vision_range -- promień widzenia (0 <==> obiekt widzi tylko siebie)
 
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
GameObjectType = recordtype('game_object_type', ['name', 'constructor', 'ID', 'vision_range'], d, doc=GameObjectType_doc)
del GameObjectType_doc, d

BASE_TYPE_ID = 4
MINER_TYPE_ID = 5
TANK_TYPE_ID = 6

BASE_TYPE = GameObjectType(ID=BASE_TYPE_ID, name='base', vision_range=16, movable=False, can_build=True, when_attacked_get_minerals=True, can_store_minerals=True,
						 	constructor=lambda player_ID: GameObject(type_ID=BASE_TYPE_ID, player_ID=player_ID))
MINER_TYPE = GameObjectType(ID=MINER_TYPE_ID, name='miner', vision_range=7, gather_size=1, cost_of_build=3,
						 	constructor=lambda player_ID: GameObject(type_ID=MINER_TYPE_ID, player_ID=player_ID, minerals=0))
TANK_TYPE = GameObjectType(ID=BASE_TYPE_ID, name='tank', vision_range=7, attack_range=3, cost_of_build=10,
						 	constructor=lambda player_ID: GameObject(type_ID=TANK_TYPE_ID, player_ID=player_ID))
					
GAME_OBJECT_TYPES_BY_ID = {
	TANK_TYPE_ID : TANK_TYPE,
	MINER_TYPE_ID : MINER_TYPE,
	BASE_TYPE_ID : BASE_TYPE,
}

OBJECT_TYPE_NAME_TO_TYPE_ID = {'TANK':TANK_TYPE_ID, 'T':TANK_TYPE_ID, 'MINER':MINER_TYPE_ID, 'M':MINER_TYPE_ID, 'BASE':BASE_TYPE_ID, 'B':BASE_TYPE_ID}



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
	{'input':'', 'output':'', 'errors_output':'', 'is_run_successful':False, 'parse_errors':'', 'executing_command_errors':''},
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

Player = recordtype('player', ['name'], {'ID':None, 'base_ID':None, 'object_IDs':[]}, doc=Player_doc)
del Player_doc



""" kierunki świata """
DIRECTION_N, DIRECTION_E, DIRECTION_S, DIRECTION_W = 'n', 'e', 's', 'w'
DIRECTION_TO_RAY = {DIRECTION_N:(0,-1), DIRECTION_E:(1,0), DIRECTION_S:(0,1), DIRECTION_W:(-1,0)}
RAY_TO_DIRECTION = {(0,-1):DIRECTION_N, (1,0):DIRECTION_E, (0,1):DIRECTION_S, (-1,0):DIRECTION_W}
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


def parse_as_int(data):
	""" W przypadku niepowodzenia zwraca None """

	if len(data)>8:
		return None
	try:
		return int(data)
	except ValueError:
		return None

def parse_as_direction(data):
	""" W przypadku niepowodzenia zwraca None w przeciwnym razie zwraca
	identyfikator kierunku świata (DIRECTION_*). """

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

def parse_as_object_type_name(data):
	""" Zwraca identyfikator typu jednostki lub None w przypadku
	niepowodzenia """
	
	type_name = parse_as_str(data, max_string_length=16)
	type_ID = OBJECT_TYPE_NAME_TO_TYPE_ID.get(type_name, None)
	return type_ID		
		


""" Klasy """
class FindPathProblem(aima.search.Problem):
    u""" Reprezentuje problem znajdowania najkrótszej ścieżki do wskazanego pola
    *lub jednego z jego sąsiadów*.
    
    """

    def __init__(self, start_position, goal, gamemap):
    	aima.search.Problem.__init__(self, start_position, goal)
        self.gamemap = gamemap

    def successor(self, state):
        x, y = state
        neightbours = []
        gamemap = self.gamemap
        goal = self.goal
        if gamemap.is_valid_position(x-1,y) and (is_flat_and_empty(gamemap[x-1][y]) or (x-1,y)==goal):
        	neightbours.append( (None, (x-1,y)) )
        if gamemap.is_valid_position(x,y-1) and (is_flat_and_empty(gamemap[x][y-1]) or (x,y-1)==goal):
        	neightbours.append( (None, (x,y-1)) )
        if gamemap.is_valid_position(x+1,y) and (is_flat_and_empty(gamemap[x+1][y]) or (x+1,y)==goal):
        	neightbours.append( (None, (x+1,y)) )
        if gamemap.is_valid_position(x,y+1) and (is_flat_and_empty(gamemap[x][y+1]) or (x,y+1)==goal):
        	neightbours.append( (None, (x,y+1)) )
       	return neightbours

    def goal_test(self, state):
        return state == self.goal

    def path_cost(self, c, state1, action, state2):
        return c + 1
        
    def h(self, node):
    	x, y = node.state
    	return distance_between((x,y), self.goal)
    	
    		

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
		""" Zwraca kierunek, w którym należy pójść od source do dest
		lub None, jeśli się	nie da dojść do celu *i żadnego jego sąsiada*
		lub gdy znajduje się już na docelowym polu. """
		
		if source == dest:
			return None
		
		problem = FindPathProblem(source, dest, self)
		result_node = aima.search.astar_search(problem)
		if result_node == None: # no path found
			return None
			
		previous_node = None
		while result_node.parent != None:
			result_node, previous_node = result_node.parent, result_node
			
		next_x, next_y = previous_node.state
		delta_x, delta_y = next_x-source[0], next_y-source[1]
		
		if is_flat_and_empty(self[next_x][next_y]):
			return RAY_TO_DIRECTION[(delta_x, delta_y)]	
	
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
		self.probability_of_mineral_deposit_growing = 0.1
		self.probability_of_successful_attack_on_alien = 0.5

		self._bash_executor = bash_executor
		self._map = game_map
		self._objects_by_ID = {}
		self._players_by_ID = {}
		self._objects_counter = Counter(1)		
		self._players_counter = Counter(1)	
		self._messages = []
		
		map(self.add_player, players)
			
	def add_player(self, player, program_for_base=None):
		"""
		Dodaje nowego gracza, bazę z minerałami na wolnej pozycji startowej
		oraz 4 minery dookoła bazy.
		
		player powinien mieć prawidłowo ustawione program_code i language_ID!
		
		Może rzucić NoFreeStartPositions.
		
		"""
	
		if program_for_base == None:
			program_for_base = Program()
	
		assert isinstance(player, Player)
		assert isinstance(program_for_base, Program)
	
		x, y = self._map.reserve_next_free_start_position() # może rzucić NoFreeStartPositions
	
		# add player
		player.ID = self._players_counter()
		self._players_by_ID[player.ID] = player

		# add base
		base = BASE_TYPE.constructor(player.ID)
		base.program = program_for_base.copy()
		base.minerals = self.minerals_for_base_at_start
		self._add_game_object(base, x, y)
		player.base_ID = base.ID
		
		# add miners
		miner = MINER_TYPE.constructor(player.ID)
		self._add_game_object(miner, x+1, y)
		self._add_game_object(miner.copy(), x-1, y)
		self._add_game_object(miner.copy(), x, y+1)
		self._add_game_object(miner.copy(), x, y-1)						
		
	def set_program(self, object_ID, program):
		assert object_ID in self._objects_by_ID
		assert isinstance(program, Program)
		
		obj = self._objects_by_ID[object_ID]
		obj.program = program
		
	def tic(self):
		self._tic_for_world()
		self._compile_and_run_programs()
		self._clear_messages()
		self._parse_programs_outputs()
		self._run_commands()
		self._answer_messages()
		
	def _tic_for_world(self):
		"""
		Modyfikuje przyrodę:
		 - odnawia złoża minerałów
		
		"""
		
		for x in xrange(self._map.size):
			for y in xrange(self._map.size):
				if has_minerals_deposit(self._map[x][y]):
					if random.random() < self.probability_of_mineral_deposit_growing:
						field = self._map[x][y]
						self._map[x][y] = put_minerals(field, get_minerals(field)+1)
		
	def _compile_and_run_programs(self):
		def make_input_for(obj):
			obj_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			vision_range = obj_type.vision_range
			input_data = '%d %d %d %d %d %d %d\n' % (
				obj.type_ID,
				obj.ID,
				obj.player_ID,
				len(obj.messages),
				obj.x, obj.y,
				obj_type.vision_range*2+1,
			)
			input_data += '%d\n' % obj.minerals \
				if obj_type.ID in (BASE_TYPE_ID, MINER_TYPE_ID) \
				else '%d\n' % obj_type.attack_range
			input_data += '\n'.join(map(' '.join,
				[	[	'%d %d %d' % (
							0 \
								if is_flat_and_empty(self._map[x][y]) \
								else 1 \
									if is_empty(self._map[x][y]) and is_upland(self._map[x][y]) \
									else 2 \
										if has_minerals_deposit(self._map[x][y]) \
										else 3 \
											if has_trees(self._map[x][y]) \
											else self._objects_by_ID[get_game_object_ID(self._map[x][y])].type_ID,
							get_minerals(self._map[x][y]) \
								if has_minerals_deposit(self._map[x][y]) \
								else get_game_object_ID(self._map[x][y]) \
									if has_game_object(self._map[x][y]) \
									else 0,
							self._objects_by_ID[get_game_object_ID(self._map[x][y])].player_ID \
								if has_game_object(self._map[x][y]) \
								else 0,
						) \
						if self._map.is_valid_position(x,y) \
						else '1 0 0'
					for y in xrange(obj.y-vision_range, obj.y+vision_range+1)]
				for x in xrange(obj.x-vision_range, obj.x+vision_range+1)]
			))
			input_data += '\n'.join(map(lambda m: '%d %s' % (m.sender_ID, m.text), obj.messages))
			return input_data
				
	
		for object_ID, obj in self._objects_by_ID.items():
			sha = hashlib.sha1()
			sha.update(obj.program.code)
			sha = sha.hexdigest()
			binary_file_path = 'cache/' + sha
			language = LANGUAGES_BY_ID[obj.program.language_ID]

			if obj.program_execution == None:
				obj.program_execution = ProgramExecution(
					compilation_errors=texts.warnings['compilation_done_in_another_session'],
					is_compilation_successful=True
				)

			input_data = make_input_for(obj)

			if language.ID == NO_LANGUAGE_ID:
				output = ''
				errors_output = ''
				is_run_successful = True
			
			else:
				# compilation
				if not os.path.exists(binary_file_path): # if compilation is needed
					s = open('cache/source', 'w')
					s.write(obj.program.code)
					s.close()
					
					_, errors_output, exit_code = self._bash_executor(language.compilation_command, 
						{'cache/source':language.source_file_name},
						{language.binary_file_name:binary_file_path},
					)
					compilation_successful = exit_code == 0
					
					obj.program_execution = ProgramExecution(
						compilation_errors=errors_output,
						is_compilation_successful=compilation_successful,
					)
			
				# run!
				if os.path.exists(binary_file_path): #obj.program_execution.is_compilation_successful:
					output, errors_output, exit_code = self._bash_executor(language.run_command, 
						{'cache/binary':language.binary_file_name},
						input_data=input_data,
					)
					is_run_successful = exit_code == 0
					
				else:
					output = ''
					errors_output = ''
					is_run_successful = False
				
			# finishing
			obj.program_execution.output = output
			obj.program_execution.errors_output = errors_output
			obj.program_execution.is_run_successful = is_run_successful
			obj.program_execution.input = input_data	
				

	def _clear_messages(self):
		self._messages = []

		for game_object in self._objects_by_ID.values():
			game_object.command = None
			game_object.messages = []		

	def _parse_programs_outputs(self):
		commands = {} # commands { <name of command> : { <number of args> : ( <signature>, <function returning (object_ID, *Command)> ) }}
		commands['stop'] = commands['s'] = {
			0 : (
					(parse_as_int,),
					lambda : StopCommand(),
				),
		}
		commands['move'] = commands['m'] = {
			2 : (
					(parse_as_direction,), 
					lambda direction: MoveCommand(direction=direction),
				),
			3 : (
					(parse_as_int, parse_as_int),
					lambda x, y: ComplexMoveCommand(destination=(x,y)),
				),
		}
		commands['gather'] = commands['g'] = {
			2 : (
					(parse_as_direction,),
					lambda direction: GatherCommand(direction=direction),
				),
			3 : (
					(parse_as_int, parse_as_int),
					lambda x, y: ComplexGatherCommand(destination=(x,y)),
				),
		}
		commands['fire'] = commands['f'] = {
			3 : (
					(parse_as_int, parse_as_int),
					lambda x, y: FireCommand(destination=(x,y)),
				),
		}
		commands['attack'] = commands['a'] = {
			3 : (
					(parse_as_int, parse_as_int),
					lambda x, y: ComplexAttackCommand(destination=(x,y)),
				),
		}
		commands['build'] = commands['b'] = {
			1 : (
					(parse_as_object_type_name,),
					lambda type_ID: BuildCommand(type_ID=type_ID, direction_or_None=None, program_object_ID_or_zero=0),
				),
			2 : (
					(parse_as_object_type_name, parse_as_int),
					lambda type_ID, object_ID: BuildCommand(type_ID=type_ID, direction_or_None=None, program_object_ID_or_zero=object_ID),
				),
		}

		for object_ID, obj in self._objects_by_ID.items():
			output = obj.program_execution.output
			obj.program_execution.parse_errors = ''
			
			for line_no, line in enumerate(output.split('\n')):
				splited_line = line.split()
				if len(splited_line) == 0: # empty line
					continue
				command_as_string = splited_line[0].lower()
				args_of_command = splited_line[1:]
				errors_info = {
					'line_no':line_no+1,
					'line':line,
					'object_ID':object_ID,
					'command':command_as_string,
					'number_of_args':len(args_of_command)
				}

				try:
					command_as_int = parse_as_int(command_as_string)
					if command_as_int != None: # mamy polecenie wysłania message zamiast komendy

						message_text = line[len(command_as_string)+1:]
						
						if command_as_int == 0:
							message = Message(sender=obj.ID, receiver_ID=0, text=message_text)
							self._messages.append(message)
						else:
							receiver = self._objects_by_ID.get(command_as_int, None)
							if receiver == None:
								raise ParseError(texts.parse_errors['cannot_send_message_invalid_receiver'] % errors_info)

							message = Message(sender_ID=obj.ID, receiver_ID=receiver.ID, text=message_text)
							receiver.messages.append(message)
							
					else: # mamy komendę, a nie polecenie wysłania message
				
						# search command
						signatures_with_functions_by_number_of_args = commands.get(command_as_string, None)
						if signatures_with_functions_by_number_of_args == None:
							raise ParseError(texts.parse_errors['unknown_command'] % errors_info)
				
						# check number of args
						signature_with_function = signatures_with_functions_by_number_of_args.get(len(args_of_command), None)
						if signature_with_function == None:
							raise ParseError(texts.parse_errors['wrong_number_of_argument'] % errors_info)
						signature, method = signature_with_function
					
						# convert args
						args = []
						for i, (function, arg) in enumerate(zip(signature, args_of_command)):
							result = function(arg)
							if result == None:
								errors_info['invalid_arg'] = arg
								errors_info['invalid_arg_no'] = i+1
								raise ParseError(texts.parse_errors['invalid_argument'] % errors_info)
							args.append(result)
				
						command = method(*args)
						self._objects_by_ID[object_ID].command = command

				except ParseError as ex:
					obj.program_execution.parse_errors += ex.args[0]
		
		# set default commands
		for obj in self._objects_by_ID.values():
			if obj.command == None:
				obj.program_execution.parse_errors += texts.warnings['no_command_for_object'] % {'object_ID':obj.ID}
				obj.command = StopCommand()
		
	def _run_commands(self):
		def execute_stop_command_of(obj, command):
			""" Patrz execute_move_command_of """
			
			obj.action = StopAction()
			
		def execute_move_command_of(obj, command):
			"""
			Wykonuje komendę command obiektu obj uwzględniając zasady gry:
			 - jeśli obiekt nie posiada umiejętności poruszania się, obiekt nie zostaje
			przemieszony,
			 - jeśli docelowe miejsce jest zajęte, nie przemieszcza obiektu,
			
			Jeśli przemieszczenie *nie* zakończyło się sukcesem, rzuca ExecutingCommandError.
			W przeciwnym razie ustawia obj.action.
			
			"""
		
			delta_x, delta_y = DIRECTION_TO_RAY[command.direction]
			dest_x, dest_y = obj.x+delta_x, obj.y+delta_y
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
			
			if not object_type.movable:
				raise ExecutingCommandError(texts.executing_command_errors['object_not_movable'] % errors_info)

			if not self._map.is_valid_position(dest_x, dest_y):
				raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)
			
			dest_field = self._map[dest_x][dest_y]
			if not is_empty(dest_field):
				raise ExecutingCommandError(texts.executing_command_errors['cannot_move_field_not_empty'] % errors_info)
		
			obj.action = MoveAction(source=(obj.x, obj.y))
			self._move_object_to(obj, (dest_x, dest_y))
		
		def execute_complex_move_command_of(obj, command):
			""" Patrz execute_move_command_of """
			
			source = (obj.x, obj.y)
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			dest_x, dest_y = command.destination
			errors_info = {'object_ID':obj.ID}

			if not object_type.movable:
				raise ExecutingCommandError(texts.executing_command_errors['object_not_movable'] % errors_info)			
			
			if not self._map.is_valid_position(dest_x, dest_y):
				raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)			
			
			if (dest_x, dest_y) == source:
				pass
			else:
				direction = self._map.find_path_from_to(source, (dest_x, dest_y))
				if direction == None:
					raise ExecutingCommandError(texts.executing_command_errors['no_path'])
				else:
					obj.action = MoveAction(source=(obj.x, obj.y))				
					self._move_object_to_direction(obj, direction)
	
		def execute_gather_command_of(obj, command):
			""" Patrz execute_move_command_of """

			direction = command.direction
			delta_x, delta_y = DIRECTION_TO_RAY[direction]
			dest_x, dest_y = obj.x + delta_x, obj.y + delta_y
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
			
			if object_type.gather_size == 0:
				raise ExecutingCommandError(texts.executing_command_errors['object_cannot_gather'] % errors_info)

			if not self._map.is_valid_position(dest_x, dest_y):
				raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)

			field = self._map[dest_x][dest_y]
		
			if not has_minerals_deposit(field):

				if not has_game_object(field):
					raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_no_minerals_deposit_neither_base'] % errors_info)

				dest_object_ID = get_game_object_ID(field)
				dest_obj = self._objects_by_ID[dest_object_ID]
				dest_obj_type = GAME_OBJECT_TYPES_BY_ID[dest_obj.type_ID]

				if not dest_obj_type.can_store_minerals:
					raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_destination_object_cannot_store_minerals'] % errors_info)
			
				obj.action = StoreAction(storage_ID=dest_object_ID)
				self._store_minerals_from_obj_to_obj(obj, dest_obj) 

			else:

				how_much_minerals_can_get_obj = object_type.gather_size-obj.minerals
				if how_much_minerals_can_get_obj == 0:
					raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_object_is_full'] % errors_info)

				how_much_minerals_in_deposit = get_minerals(field)
				if how_much_minerals_in_deposit == 0:
					raise ExecutingCommandError(texts.executing_command_errors['cannot_gather_mineral_deposit_is_empty'] % errors_info)
			
				obj.action = GatherAction(destination=(dest_x, dest_y))
				how_much_minerals = min(how_much_minerals_can_get_obj, how_much_minerals_in_deposit)
				self._store_minerals_from_deposit_to_obj((dest_x, dest_y), obj, how_much_minerals)
		
		def execute_complex_gather_command_of(obj, command):
			""" Patrz execute_move_command_of """
			
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			player = self._players_by_ID[obj.player_ID]
			errors_info = {'object_ID':obj.ID}
			
			if object_type.gather_size == 0:
				raise ExecutingCommandError(texts.executing_command_errors['object_cannot_gather'] % errors_info)
				
			if not object_type.movable:
				raise ExecutingCommandError(texts.executing_command_errors['object_not_movable'] % errors_info)		

			if obj.minerals < object_type.gather_size:
				dest_x, dest_y = command.destination
				
				if not self._map.is_valid_position(dest_x, dest_y):
					raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)
					
				field = self._map[dest_x][dest_y]
				if not has_minerals_deposit(field):
					raise ExecutingCommandError(texts.executing_command_errors['cannot_complex_gather_destination_has_no_deposit'] % errors_info)
				
				if distance_between((obj.x, obj.y), (dest_x, dest_y)) == 1:
					obj.action = GatherAction(destination=(dest_x, dest_y))
					self._store_minerals_from_deposit_to_obj((dest_x, dest_y), obj, 1)
				else:
					direction = self._map.find_path_from_to((obj.x, obj.y), (dest_x, dest_y))
					if direction == None:
						raise ExecutingCommandError(texts.executing_command_errors['no_path'])
					else:
						obj.action = MoveAction(source=(obj.x, obj.y))
						self._move_object_to_direction(obj, direction)
				
			else:
				base = self._objects_by_ID.get(player.base_ID, None)
				if base == None:
					raise ExecutingCommandError(texts.executing_command_errors['no_base_no_gather'] % errors_info)
					
				if distance_between((obj.x, obj.y), (base.x, base.y)) == 1:
					obj.action = StoreAction(storage_ID=base.ID)
					self._store_minerals_from_obj_to_obj(obj, base)
				else:
					direction = self._map.find_path_from_to((obj.x, obj.y), (base.x, base.y))
					if direction == None:
						raise ExecutingCommandError(texts.executing_command_errors['no_path'] % errors_info)
					else:
						obj.action = MoveAction(source=(obj.x, obj.y))					
						self._move_object_to_direction(obj, direction)
			
		def execute_fire_command_of(obj, command):
			""" Patrz execute_move_command_of """

			dest_x, dest_y = command.destination
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
						
			if object_type.attack_range == 0:
				raise ExecutingCommandError(texts.executing_command_errors['object_cannot_attack'] % errors_info)
			
			if not self._map.is_valid_position(dest_x, dest_y):
				raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)
				
			distance = distance_between((obj.x,obj.y),(dest_x,dest_y))
			if object_type.attack_range < distance:
				errors_info['distance'], errors_info['attack_range'] = distance, object_type.attack_range
				raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_destination_too_far'] % errors_info)
			if distance == 0:
				raise ExecutingCommandError(texts.executing_command_errors['cannot_attack_itself'] % errors_info)
		
			obj.action = FireAction(destination=(dest_x, dest_y))
			self._attack(dest_x, dest_y)

		def execute_complex_attack_command_of(obj, command):
			""" Patrz execute_move_command_of """
			
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			dest_x, dest_y = command.destination
			errors_info = {'object_ID':obj.ID, 'x':dest_x, 'y':dest_y}
			
			if object_type.attack_range == 0:
				raise ExecutingCommandError(texts.executing_command_errors['object_cannot_attack'] % errors_info)
				
			if not self._map.is_valid_position(dest_x, dest_y):
				raise ExecutingCommandError(texts.executing_command_errors['invalid_position'] % errors_info)			
				
			if not object_type.movable:
				raise ExecutingCommandError(texts.executing_command_errors['object_not_movable'] % errors_info)
				
			dest_field = self._map[dest_x][dest_y]
			if has_game_object(dest_field):
				dest_object = self._objects_by_ID[get_game_object_ID(dest_field)]
				if dest_object.player_ID == obj.player_ID:
					raise ExecutingCommandError(texts.executing_command_errors['attacking_your_objects_stopped'] % errors_info)
				else:
					obj.action = FireAction(destination=(dest_x, dest_y))
					self._attack(dest_x, dest_y)
			
			else:
				the_nearest_alien = _get_the_nearest_alien_in_attack_range_to(obj)
				if the_nearest_alien != None:
					obj.action = FireAction(destination=(the_nearest_alien.x, the_nearest_alien.y))
					self._attack(the_nearest_alien.x, the_nearest_alien.y)
				else:
					direction = self._map.find_path_from_to((obj.x, obj.y), (dest_x, dest_y))
					if direction == None:
						raise ExecutingCommandError(texts.executing_command_errors['no_path'])
					else:
						obj.action = MoveAction(source=(obj.x, obj.y))					
						self._move_object_to_direction(obj, direction)					
					

		def execute_build_command_of(builder_object, command):
			""" Patrz execute_move_command_of """

			type_ID, direction_or_None = command.type_ID, command.direction_or_None
			object_type = GAME_OBJECT_TYPES_BY_ID[type_ID]

			dest_x, dest_y = builder_object.x, builder_object.y
			if direction_or_None == None:
				destinations = [(dest_x, dest_y-1), (dest_x+1, dest_y), (dest_x, dest_y+1), (dest_x-1, dest_y)]
			else:
				delta_x, delta_y = DIRECTION_TO_RAY[direction_or_None]
				destinations = [(dest_x+delta_x, dest_y+delta_y)]

			built_object_type = GAME_OBJECT_TYPES_BY_ID[type_ID]
			builder_object_type = GAME_OBJECT_TYPES_BY_ID[builder_object.type_ID]
			errors_info = {'object_ID':builder_object.ID, 'built_object_name':built_object_type.name}		

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
						# build object
						built_object = built_object_type.constructor(builder_object.player_ID)
						builder_object.minerals -= built_object_type.cost_of_build
						builder_object.action = BuildAction(type_ID=built_object_type, destination=(dest_x, dest_y))
						self._add_game_object(built_object, dest_x, dest_y)

						if command.program_object_ID_or_zero != 0:
							program_object = self._objects_by_ID.get(command.program_object_ID_or_zero, None)
							if program_object == None:
								raise ExecutingCommandError(texts.executing_command_errors['build_warning_unknown_object_ID'] % errors_info)
							built_object.program = program_object.program.copy()
						return
			raise ExecutingCommandError(texts.executing_command_errors['cannot_build_no_free_space'] % errors_info)			
	
		def _get_the_nearest_alien_in_attack_range_to(obj):
			obj_x, obj_y = obj.x, obj.y
			object_type = GAME_OBJECT_TYPES_BY_ID[obj.type_ID]
			attack_range = object_type.attack_range
			
			the_distance = 9999999
			the_nearest_alien = None
			for x in xrange(obj_x-attack_range, obj_x+attack_range+1):
				for y in xrange(obj_y-attack_range, obj_y+attack_range+1):
					if self._map.is_valid_position(x, y) and distance_between((x,y), (obj_x, obj_y)) <= attack_range:
						field = self._map[x][y]
						if has_game_object(field):
							alien = self._objects_by_ID[get_game_object_ID(field)]
							if obj.player_ID != alien.player_ID:
								distance = distance_between((x, y), (obj_x, obj_y))
								if distance < the_distance:
									the_distance = distance
									the_nearest_alien = alien
								
			return the_nearest_alien
	
		commands = {
			StopCommand : execute_stop_command_of,
			MoveCommand : execute_move_command_of,
			ComplexMoveCommand : execute_complex_move_command_of,
			GatherCommand : execute_gather_command_of,
			ComplexGatherCommand : execute_complex_gather_command_of,
			FireCommand : execute_fire_command_of,
			ComplexAttackCommand : execute_complex_attack_command_of,
			BuildCommand : execute_build_command_of,															
		}
	
		for obj in self._objects_by_ID.values():
			obj.program_execution.executing_command_errors = ''	
	
		objects_by_ID = self._objects_by_ID.keys()
		random.shuffle(objects_by_ID)
		for object_ID in objects_by_ID:
			obj = self._objects_by_ID.get(object_ID, None)
			if obj == None: # jednostka mogła już zostać zniszczona przez atak innej jednostki; usunięcie jednostki z self._objects_by_ID nie ma wpływu na objects_by_ID
				continue
			obj.action = StopAction()
			
			try:
				method = commands[obj.command.__class__]
				method(obj, obj.command)
			except ExecutingCommandError as ex:
				obj = self._objects_by_ID[obj.player_ID]
				obj.program_execution.executing_command_errors += ex.args[0]

	def _answer_messages(self):
		""" Odpowiada na messages z zapytaniami wysłane do systemu gry. """
		
		for message in self._messages:
			text = message.text
			sender_ID = message.sender_ID
			sender = self._objects_by_ID.get(sender_ID, None)
			if sender == None:
				continue
				
			splited_text = text.split()
			if (len(splited_text) == 2 and splited_text[0].lower() == 'list' and splited_text[1].lower() == 'units') \
				or (len(splited_text) == 1 and splited_text[0].lower() == 'lu'):
				
				player = self._players_by_ID[sender.player_ID]
				answer_text = "%d " % len(player.object_IDs)
				for object_ID in player.object_IDs:
					object_type = self._objects_by_ID[object_ID].type_ID
					answer_text += "%d %d " % (object_ID, object_type)
				
			elif (len(splited_text) == 2 and splited_text[0].lower() in ('unit', 'u')):
				unit_ID = parse_as_int(splited_text[1])
				if unit_ID == None:
					continue
				
				unit = self._objects_by_ID.get(unit_ID, None)
				if unit == None:
					continue
					
				answer_text = "%d %d %d %d %d" % (
					unit.ID,
					unit.type_ID,
					unit.x, unit.y,
					unit.minerals if unit.type_ID != TANK_TYPE_ID else GAME_OBJECT_TYPES_BY_ID[unit.type_ID].attack_range,
				)
				
			answer = Message(sender_ID=0, receiver_ID=sender_ID, text=answer_text)
			sender.messages.append(answer)				
	

	def _attack(self, dest_x, dest_y):
		""" Atakuje zadane pole """
	
		field = self._map[dest_x][dest_y]
		if has_trees(field):
			self._map[dest_x][dest_y] = erase_object(field)
		elif has_game_object(field):
			obj = self._objects_by_ID[get_game_object_ID(field)]
			if GAME_OBJECT_TYPES_BY_ID[obj.type_ID].when_attacked_get_minerals and obj.minerals > 0:
				obj.minerals -= 1
			else:
				if random.random() < self.probability_of_successful_attack_on_alien:
					self._remove_game_object_at(dest_x, dest_y)
	
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

	def _move_object_to(self, obj, dest):
		""" * Nie zmienia obj.action! * 
		Sprawdza jedynie czy pole jest puste (może rzucić NotEmptyFieldException) """
	
		if not is_empty(self._map[dest[0]][dest[1]]):
			raise NotEmptyFieldException()
	
		self._map[obj.x][obj.y] = erase_object(self._map[obj.x][obj.y])
		obj.x, obj.y = dest[0], dest[1]
		self._map[obj.x][obj.y] = put_game_object(self._map[obj.x][obj.y], obj.ID)
		
	def _move_object_to_direction(self, obj, direction):
		""" Przemieszcza obiekt o jedno pole we wskazanym kierunku świata. 
		Sprawdza jedynie czy pole jest puste (może rzucić NotEmptyFieldException) """
		
		delta_x, delta_y = DIRECTION_TO_RAY[direction] 
		next_x, next_y = delta_x+obj.x, delta_y+obj.y
		self._move_object_to(obj, (next_x, next_y)) # may raise NotEmptyFieldException		
		
	def _store_minerals_from_obj_to_obj(self, obj, dest_obj):
		""" Nie rzuca wyjątków, nie sprawdza nic! """
	
		dest_obj.minerals += obj.minerals
		obj.minerals = 0
		
	def _store_minerals_from_deposit_to_obj(self, (source_x, source_y), dest_obj, how_much_minerals):
		dest_obj.minerals += how_much_minerals
		field = self._map[source_x][source_y]
		self._map[source_x][source_y] = put_minerals(field, get_minerals(field)-how_much_minerals)
		
	def _remove_game_object_at(self, x, y):
		""" Nie rzuca wyjątków, nie sprawdza nic! """
	
		field = self._map[x][y]
		object_ID = get_game_object_ID(field)
		obj = self._objects_by_ID[object_ID]
		self._map[x][y] = erase_object(field)
		del self._objects_by_ID[object_ID]		

		player = self._players_by_ID[obj.player_ID]
		player.object_IDs.remove(object_ID)
		if player.base_ID == object_ID:
			player.base_ID = None		


