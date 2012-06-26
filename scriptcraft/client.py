#!/usr/bin/env python
#-*- coding:utf-8 -*-

try:
    import cPickle as pickle
except:
    import pickle
import itertools
import math
import os.path
import random
from Tkinter import *
import tkColorChooser
import tkFileDialog
import tkFont
import tkMessageBox
import tkSimpleDialog
from PIL import Image, ImageTk # it overrides Tkinter.Image so it must be after Tkinter import statement

from scriptcraft import direction
from scriptcraft.gamemap import GameMap
from scriptcraft.gamestate import (actions, Game, DEFAULT_GAME_CONFIGURATION,
                                   Language, Program, STAR_PROGRAM, Unit,
                                   NoFreeStartPosition, Tree, MineralDeposit,
                                   load_game_map, InvalidGameMapData)
from scriptcraft.gamesession import GameSession, SystemConfiguration
from scriptcraft.utils import *



class GameViewer(Canvas):
    """GameViewer is canvas widget to display a scriptcraft Game
    instance. It provides scrolling and zooming the map and selecting
    fields.

    About selecting:

    When a field is being selected (or the selection was selected
    again), <<field-selected>> event is sent. The selected position
    (in integer game coordinates) is stored in pointer_position
    attribute.

    If the user click out of map and an selection exists, then the
    existing selection is removed and <<selection-removed>> event is
    sent. In this case pointer_position attribute is None.
    """

    SCROLLING_SENSITIVITY = 1.15 # in (1, +inf); greater means faster scrolling
    TILE_WIDTH = 64
    TILE_HEIGHT = 32
    GROUND_TILE_WIDTH = 32
    GROUND_TILE_HEIGHT = 32
    GROUND_TILES_IN_ROW = 4
    GROUND_TILES_IN_COLUMN = 4
    GROUND_TYPE_TO_NAME = {
        0:'ground-black',
        1:'ground-dirt',
        2:'ground-grass',
        3:'ground-rock',
        4:'ground-stones',
        5:'ground-flowers',
        6:'ground-hardearth',
        7:'ground-tiles',
        8:'ground-sand',
    }

    def __init__(self, master):
        Canvas.__init__(self, master, width=800, height=600, bg='black')
        self.pack(expand=YES, fill=BOTH)

        # To enable receiving wheel rolling events under windows, we
        # need this action before bindings:
        self.focus_set()

        # bindings
        self.bind('<B1-Motion>', self._mouse_motion_callback)
        self.bind('<ButtonRelease-1>', self._release_callback)
        self.bind('<MouseWheel>', self._roll_wheel_callback)
        self.bind('<Button-4>', self._roll_wheel_callback)
        self.bind('<Button-5>', self._roll_wheel_callback)
        self.bind('<Button-1>', self._click_callback)

        # own attributes
        self._zoom = 1.0
        self._delta = (-5.0, 0.0)
        self._game = None
        self._scaled_images_cache = {}
        self._ground_image_cache = None
        self._ground_tiles_cache = {}
        self._last_mouse_position = None # None unless button pressed
        self._click_position = None
        self.selection_position = None # None or (x, y)

    @log_on_enter('set game in game viewer', mode='only time')
    def set_game(self, game):
        """ Attribute game should be scriptcraft game instance or
        None.

        In this method game instance passed during previous
        call is used. The previous game instance cannot be modified
        since the previous call!
        """

        previous_game = self._game
        self._game = game

        if previous_game:
            self.delete(ALL)

        if not game:
            self._set_selection_position(None)

        else:
            redraw_ground = (previous_game is None or
                             previous_game.game_map is not game.game_map)
            if redraw_ground:
                self._ground_image_cache = None
            self._draw_game(game)
            self._set_selection_position(self.selection_position)

    def _draw_game(self, game, redraw_ground=True):
        def draw_arrow_from_to(source, destination):
            delta = map(lambda (a, b): a-b, zip(destination,
                                                source))
            d = direction.FROM_RAY[tuple(delta)]
            direction_name = direction.TO_FULL_NAME[d]
            self._draw('arrow-red-%s' % direction_name, source, layer=2)

        self._draw('ground', (0, 0), layer=1)

        # draw objects
        for position in itertools.product(xrange(game.game_map.size[0]),
                                          xrange(game.game_map.size[1])):
            field = game.game_map[position]
            obj = field.maybe_object

            if isinstance(obj, MineralDeposit): # draw minerals
                if obj.minerals:
                    self._draw('minerals', position, layer=3)
                else:
                    self._draw('minerals-ex', position, layer=3)

            if isinstance(obj, Tree): # draw trees
                name = 'tree%s' % obj.type
                self._draw(name, position, layer=3)

            if isinstance(obj, Unit): # draw unit
                unit = obj

                # build sprite name
                if unit.type.main_name == '4': # base
                    sprite_name = 'base'
                elif unit.type.main_name == '5': # miner
                    storage_state = 'loaded' if unit.minerals else 'empty'
                    direction_name = direction.TO_FULL_NAME[unit.direction]
                    sprite_name = 'miner-%s-%s' % \
                      (storage_state, direction_name)
                elif unit.type.main_name == '6':
                    direction_name = direction.TO_FULL_NAME[unit.direction]
                    sprite_name = 'tank-%s' % direction_name
                else:
                    assert False, 'oops, unknown unit type %r' % unit.type

                # draw the unit
                if isinstance(unit.action, actions.MoveAction):
                    middle = lambda p1, p2: ((p1[0]+p2[0])/2.0,
                                             (p1[1]+p2[1])/2.0)
                    position = middle(unit.action.source,
                                      unit.action.destination)

                self._draw(sprite_name, position, layer=3)

                # draw label for the unit
                x, y = self._to_screen_coordinate(position)
                color = '#' + "%02x%02x%02x" % unit.player.color
                font = self._get_font_for_current_zoom()
                self.create_text(x, y, fill=color, text=unit.player.name,
                                 font=font, tags=['text'],
                                 state=NORMAL if font else HIDDEN)

                # draw arrows indicating executing action (or fire explosion)
                if isinstance(unit.action, actions.GatherAction):
                    draw_arrow_from_to(unit.position, unit.action.source)
                elif isinstance(unit.action, actions.StoreAction):
                    destination_unit = self._game.units_by_IDs[
                        unit.action.storage_ID]
                    destination = destination_unit.position
                    draw_arrow_from_to(unit.position, destination)
                elif isinstance(unit.action, actions.FireAction):
                    self._draw('explosion', unit.action.destination, layer=3)

        with log_on_enter('raising layers', mode='only time'):
            self.tag_raise('layer-1')
            self.tag_raise('layer-2')
            self.tag_raise('layer-3')
            self.tag_raise('text')

        # draw lines (debug)
        def draw_grid():
            for x in xrange(0, game.game_map.size[1] + 1):
                start_position = (0, x)
                end_position = (game.game_map.size[0], x)
                start_position = self._to_screen_coordinate(start_position)
                end_position = self._to_screen_coordinate(end_position)
                self.create_line(*(start_position + end_position), fill='white')

            for y in xrange(0, game.game_map.size[0] + 1):
                start_position = (y, 0)
                end_position = (y, game.game_map.size[1])
                start_position = self._to_screen_coordinate(start_position)
                end_position = self._to_screen_coordinate(end_position)
                self.create_line(*(start_position + end_position), fill='white')

        #draw_grid()

    @memoized
    def _gradient(self, align):
        assert align in ('ns', 'we')
        gradient = Image.new('L', (255, 1))
        for x in range(255):
            gradient.putpixel((254-x, 0), x)
        gradient = gradient.resize((255, 255))
        if align == 'ns':
            gradient = gradient.rotate(-45, expand=True)
        elif align == 'we':
            gradient = gradient.rotate(45+180, expand=True)
        gradient = gradient.resize((GameViewer.TILE_WIDTH+2,
                                    GameViewer.TILE_HEIGHT+2))
        return gradient

    def _set_selection_position(self, new_position):
        """ Create or move exisitng pointer. Argument new_position can
        be None if you want to disable the pointer. """

        #self.delete('selection')
        #state = HIDDEN if new_position is None else NORMAL
        #self._draw('pointer', new_position or (0, 0),
        #           state=state, extra_tags=['selection'])
        self.selection_position = new_position

    def _draw(self, name, position, layer, state=NORMAL, extra_tags=None):
        """ Draw sprite with name 'name' at position 'position' in
        game coordinates."""

        extra_tags = extra_tags or []
        tags = [name, 'layer-%s' % layer]
        position = self._to_screen_coordinate(position)
        x, y = self._to_image_position(name, position)
        image = self._get_scaled_sprite(name)
        self.create_image(x, y, image=image, anchor=NW,
                          state=state, tags=tags+extra_tags)

    def _get_font_for_current_zoom(self):
        size = int(15*self._zoom)
        if size < 10:
            if size >= 6:
                return tkFont.Font(size=10)
            else:
                return None
        else:
            return tkFont.Font(size=size)

    @memoized
    def _get_image(self, name):
        """ Return (PIL.)Image instance. """
        path = 'graphic/%s.png' % name
        image = Image.open(datafile_path(path))
        return image

    @log_on_enter('debug get ground tile', mode='only time')
    def _get_ground_tile(self, name, (x, y)):
        x %= GameViewer.GROUND_TILES_IN_ROW
        y %= GameViewer.GROUND_TILES_IN_COLUMN

        key = (name, (x, y))
        if key not in self._ground_tiles_cache:
            start_point_x = x*GameViewer.GROUND_TILE_WIDTH
            start_point_y = y*GameViewer.GROUND_TILE_HEIGHT
            image = self._get_image(name)
            image = image.convert('RGBA')
            box = (start_point_x, start_point_y,
                GameViewer.GROUND_TILE_WIDTH+start_point_x,
                GameViewer.GROUND_TILE_HEIGHT+start_point_y)
            croped = image.crop(box)
            rotated = croped.rotate(45, expand=True)
            scaled = rotated.resize((GameViewer.TILE_WIDTH+2,
                                     GameViewer.TILE_HEIGHT+2))
            self._ground_tiles_cache[key] = scaled
        return self._ground_tiles_cache[key]

    @log_on_enter('debug computing ground image', mode='only time')
    def _get_ground_image(self):
        """ Return (PIL.)Image instance. """

        if self._ground_image_cache is None: # then compute it and cache
            log('computing ground image')

            def blend(image_nw, image_ne, image_se, image_sw,
                gradient_ns, gradient_we):
                image_w = Image.composite(image_nw, image_sw, gradient_ns)
                image_e = Image.composite(image_ne, image_se, gradient_ns)
                return Image.composite(image_w, image_e, gradient_we)

            gradient_ns = self._gradient('ns')
            gradient_we = self._gradient('we')

            size = self._game.game_map.size
            image_size = (GameViewer.TILE_WIDTH/2.0*(size[0]+size[1]+2),
                          GameViewer.TILE_HEIGHT/2.0*(size[0]+size[1]+2))
            result = Image.new('RGB', map(int, image_size))
            game_map = self._game.game_map

            for (x, y) in itertools.product(xrange(-1, size[0]),
                                              xrange(-1, size[1])):

                ground_type_nw = game_map[x, y].ground_type or 0
                ground_type_ne = game_map[x+1, y].ground_type or 0
                ground_type_se = game_map[x+1, y+1].ground_type or 0
                ground_type_sw = game_map[x, y+1].ground_type or 0

                tile_name_nw = GameViewer.GROUND_TYPE_TO_NAME[ground_type_nw]
                tile_name_ne = GameViewer.GROUND_TYPE_TO_NAME[ground_type_ne]
                tile_name_se = GameViewer.GROUND_TYPE_TO_NAME[ground_type_se]
                tile_name_sw = GameViewer.GROUND_TYPE_TO_NAME[ground_type_sw]

                tile_nw = self._get_ground_tile(tile_name_nw, (x, y))
                tile_ne = self._get_ground_tile(tile_name_ne, (x+1, y))
                tile_se = self._get_ground_tile(tile_name_se, (x+1, y+1))
                tile_sw = self._get_ground_tile(tile_name_sw, (x, y+1))

                tile = blend(tile_nw, tile_ne, tile_se, tile_sw,
                             gradient_ns, gradient_we)
                box = [GameViewer.TILE_WIDTH/2.0*(-x+y+size[1]),
                       GameViewer.TILE_HEIGHT/2.0*(x+y+2)]
                result.paste(tile, tuple(map(int, box)), tile)

            self._ground_image_cache = result
        return self._ground_image_cache

    def _get_scaled_sprite(self, name):
        """ Return (PIL.)ImageTk scaled by self._zoom factor. """

        # if cached, return cached value
        image = self._scaled_images_cache.get(name, None)
        if image:
            return image

        # otherwise compute, cache and return
        if name == 'ground':
            image = self._get_ground_image()
        else:
            image = self._get_image(name)
        width, height = image.size
        new_width, new_height = (int(width*self._zoom+2),
                                 int(height*self._zoom+2))
        image = image.resize((new_width, new_height), Image.NEAREST)
        image = ImageTk.PhotoImage(image)

        # no problem with bug connected with reference count --
        # caching keeps image reference
        self._scaled_images_cache[name] = image
        return image

    def _to_screen_coordinate(self, (x, y)):
        """ From game coordinates. """
        return (32*self._zoom*(x-y-2*self._delta[0]),
                16*self._zoom*(x+y-2*self._delta[1]))

    def _to_game_coordinate(self, (x, y)):
        """ From screen coordinates. """
        return (x/64.0/self._zoom + y/32.0/self._zoom \
                + self._delta[0] + self._delta[1],
                -x/64.0/self._zoom + y/32.0/self._zoom \
                - self._delta[0] + self._delta[1])

    def _to_image_position(self, image_name, (x, y)):
        """ From screen coordinaties. """
        if image_name == 'ground':
            dx = GameViewer.TILE_WIDTH/2.0 * (self._game.game_map.size[1]+1)
            dy = GameViewer.TILE_HEIGHT/2.0
        else:
            switch = {
                'tank' : (22, 0),
                'miner' : (18, 3),
                'base' : (31, 13),
                'minerals' : (20, 10),
                'tree1' : (10, 45),
                'tree2' : (20, 25),
                'tree3' : (20, 40),
                'tree4' : (15, 25),
                'tree5' : (18, 15),
                'tree6' : (22, 18),
                'arrow' : (32, 0),
                'explosion' : (10, -5),}
            first_part = image_name.split('-', 1)[0]
            dx, dy = switch[first_part]
        return x-dx*self._zoom, y-dy*self._zoom

    @log_on_enter('GameViewer._set_zoom', mode='only time')
    def _set_zoom(self, zoom, (XS, YS)):
        """ Set zoom. The point (XS, YS) in screen coordinate doesn't
        move."""

        # It clears cache of scaled images. Due to reference count bug
        # all images will be removed from memory!

        # compute new self._delta and self._zoom
        xS, yS = self._to_game_coordinate((XS, YS))
        self._delta = [-XS/64.0/zoom + xS/2.0 - yS/2.0,
                       -YS/32.0/zoom + xS/2.0 + yS/2.0]
        self._zoom, old_zoom = zoom, self._zoom

        # scale all images
        with log_on_enter('GameViewer._set_zoom: rescaling', mode='only time'):
            names = self._scaled_images_cache.keys()
            self._scaled_images_cache = {} # clear cache
            for name in names:
                image = self._get_scaled_sprite(name)
                self.itemconfigure(name, image=image)

        # scale all texts
        font = self._get_font_for_current_zoom()
        self.itemconfigure('text', font=font,
                            state = NORMAL if font else HIDDEN)

        # move all images
        factor = zoom/old_zoom
        self.scale(ALL, XS, YS, factor, factor)

    def _roll_wheel_callback(self, event):
        if self._game:
            delta = 0
            if event.num == 5: # respond Linux wheel event
                delta -= 1
            elif event.num == 4: # -//-
                delta += 1
            else: # respond Windows wheel event
                delta += event.delta // 120

            factor = GameViewer.SCROLLING_SENSITIVITY**delta
            self._set_zoom(self._zoom*factor, (event.x, event.y))

    def _mouse_motion_callback(self, event):
        if self._game and self._last_mouse_position:
            with log_on_enter('moving everything', mode='only time'):
                dx, dy = (event.x - self._last_mouse_position[0],
                    event.y - self._last_mouse_position[1])
                self.move(ALL, dx, dy)
                self._delta = (self._delta[0]-dx/64.0/self._zoom,
                               self._delta[1]-dy/32.0/self._zoom)

        self._last_mouse_position = (event.x, event.y)

    def _click_callback(self, event):
        if self._game:
            self._click_position = (event.x, event.y)

    def _release_callback(self, event):
        self._last_mouse_position = None

        if self._click_position:
            release_position = (event.x, event.y)
            if self._click_position == release_position:
                self._single_click_callback(event)

    def _single_click_callback(self, event):
        if self._game:
            click_position = self._to_game_coordinate((event.x, event.y))
            integer_click_position = map(lambda i: int(math.floor(i)),
                                         click_position)
            integer_click_position = tuple(integer_click_position)
            if self._game.game_map[integer_click_position].valid_position:
                self._set_selection_position(integer_click_position)
                self.event_generate("<<field-selected>>")
            elif self.selection_position:
                self._set_selection_position(None)
                self.event_generate("<<selection-removed>>")



DEFAULT_SYSTEM_CONFIGURATION = SystemConfiguration()


class ClientApplication(Frame):

    MENU_GAME_LABEL = "Gra"
    NEW_GAME_LABEL = "Stwórz nową grę..."
    SAVE_GAME_LABEL = "Zapisz grę"
    LOAD_GAME_LABEL = "Wczytaj grę..."
    ADD_PLAYER_LABEL = "Dodaj nowego gracza..."
    SET_PROGRAM_LABEL = "Ustaw program zaznaczonej jednostce..."
    SET_STAR_PROGRAM_LABEL = "Ustaw star program zaznaczonej jednostce"
    DELETE_PROGRAM_LABEL = "Usuń program zaznaczonej jednostce"
    TIC_LABEL = "Symuluj jedną turę gry"
    QUIT_LABEL = "Wyjdź"

    MENU_ABOUT_LABEL = "O grze"

    CHOOSE_MAP_FILE = 'Wybierz mapę'
    CHOOSE_DIRECTORY_FOR_NEW_GAME = "Wybierz folder dla nowej gry"
    TITLE_CREATE_NEW_GAME = 'Stwórz nową grę'
    CANNOT_CREATE_NEW_GAME = 'Nie można stworzyć nowej gry.'
    CANNOT_OPEN_FILE = ('Nie można otworzyć pliku '
                        '(być może nie masz wystarczających uprawnień).')
    MAP_FILE_IS_CORRUPTED = 'Plik mapy jest uszkodzony.'
    IO_ERROR_DURING_READING = 'Wystąpił błąd podczas czytania pliku.'
    TITLE_SAVE_GAME = 'Zapisz grę'
    CANNOT_SAVE_GAME = 'Nie można zapisać gry.'
    IO_ERROR_DURING_SAVING = 'Wystąpił błąd podczas zapisywania pliku.'
    TITLE_LOAD_GAME = 'Wczytaj grę'
    CANNOT_LOAD_GAME = 'Nie można wczytać gry.'
    TITLE_CREATE_PLAYER = 'Dodaj nowego gracza'
    ENTER_NEW_PLAYER_NAME = 'Wpisz nazwę nowego gracza.'
    TITLE_CREATE_PLAYER_CHOOSE_COLOR = 'Wybierz kolor dla nowego gracza.'
    CANNOT_CREATE_PLAYER = 'Nie można dodać nowego gracza.'
    NO_FREE_START_POSITION = \
      'Wszystkie pozycje startowe na mapie są już zajęte.'
    TITLE_CHOOSE_SOURCE_FILE = 'Wybierz plik źródłowy'
    TITLE_SET_PROGRAM = 'Ustaw program'
    CANNOT_SET_PROGRAM = 'Nie można ustawić programu.'
    UNKNOWN_SOURCE_FILE_EXTENSION = 'Nieznane rozszerzenie pliku źródłowego.'
    TITLE_ARE_YOU_SURE = 'Czy jesteś pewien?'
    WARNING_CURRENT_GAME_WILL_BE_LOST = \
      'Czy jesteś pewien? Aktualna gra zostanie bezpowrotnie utracona.'
    TITLE_QUIT_PROGRAM = 'Wyjdź z programu'
    QUIT_PROGRAM_QUESTION = 'Czy na pewno chcesz wyjść z programu?'
    ABOUT_TITLE = 'O grze'
    ABOUT_CONTENT = ('Scriptcraft - gra programistyczna.\n\n'
                     'Właścicielem grafiki i map jest Marek Szykuła. '
                     'Nie mogą być one kopiowane ani rozpowszechniane. \n\n'
                     'Kod źródłowy jest na licencji GPLv3 '
                     'i może być rozpowszechniany i kopiowany.')


    MAP_FILE_TYPES = (
        ('Plik mapy', '*.map'),
        ('Wszystkie pliki', '*')
    )

    DEFAULT_PLAYER_COLORS = (
        (178, 146, 0),
        (128, 0, 0),
        (0, 255, 220),
        (255, 0, 255),
        (0, 0, 255),
        (0, 200, 0),
        (255, 255, 0),
        (255, 0, 0), # the last one is get as the first one
    )

    # initializing --------------------------------------------------------

    def __init__(self, master):
        Frame.__init__(self, master)
        self._init_gui()
        self._game = None
        self._game_session = None
        self._load_testing_game()

    @log_on_enter('load game for testing')
    def _load_testing_game(self):
        filename = datafile_path('maps/small.map')

        # create game_map
        #game_map = load_game_map(open(filename, 'r').read())

        def generate_simple_map():
            import random
            size = 96
            game_map = GameMap((size, size), [(10, 10), (53, 10), (10, 53), (53, 53)])
            number_of_trees = 0
            for x in xrange(size):
                for y in xrange(size):
                    p = 0.0
                    if (6 <= x <= 14 or 49 <= x <= 57 or
                        6 <= y <= 14 or 49 <= y <= 57):
                        p = 0.0
                    if (random.random() < p):
                        number_of_trees += 1
                        game_map[x, y].place_object(Tree())
                    game_map[x, y].change_ground(random.randint(1, 8))
            log('map size: %d, number of fields: %d' % (size, size**2))
            log('number of trees: %d' % number_of_trees)
            return game_map

        game = None
        #game = Game(generate_simple_map(), DEFAULT_GAME_CONFIGURATION)

        # create game and game session
        session = GameSession(
            directory='scriptcraft/.tmp',
            system_configuration=DEFAULT_SYSTEM_CONFIGURATION,
            game=game)
        self.set_game_session(session)
        game = session.game

        # modify game (add players)
        game.new_player_with_units('Bob', self._reserve_color())
        game.new_player_with_units('Alice', self._reserve_color())

        def set_program(unit_id, filename):
            program = Program(Language.PYTHON,
                              open('scriptcraft/.tmp/'+filename).read())
            game.set_program(game.units_by_IDs[unit_id], program)
        set_program(8, 'build_tank.py')
        for i in xrange(3,7):
            set_program(i, 'move_randomly.py')
        for i in xrange(9,13):
            set_program(i, 'move_randomly.py')

        self._set_game(game)

    def _init_gui(self):
        self.pack(expand=YES, fill=BOTH)
        global root
        root.protocol("WM_DELETE_WINDOW", self._quit_callback)
        self._create_menubar()
        self._create_keyboard_shortcuts()
        self._game_viewer = GameViewer(self)
        self._game_viewer.bind('<<field-selected>>',
                               self._field_select_callback)
        self._game_viewer.bind('<<selection-removed>>',
                               self._selection_removal_callback)

    def _create_menubar(self):
        menubar = Menu(self)

        self._game_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=ClientApplication.MENU_GAME_LABEL,
                            menu=self._game_menu)
        self._game_menu.add_command(
            label=ClientApplication.NEW_GAME_LABEL,
            command=self._new_game_callback)
        self._game_menu.add_command(
            label=ClientApplication.SAVE_GAME_LABEL,
            command=self._save_game_callback,
            state=DISABLED)
        self._game_menu.add_command(
            label=ClientApplication.LOAD_GAME_LABEL,
            command=self._load_game_callback)
        self._game_menu.add_separator()
        self._game_menu.add_command(
            label=ClientApplication.ADD_PLAYER_LABEL,
            command=self._add_player_callback,
            state=DISABLED)
        self._game_menu.add_command(
            label=ClientApplication.DELETE_PROGRAM_LABEL,
            command=self._delete_program_callback,
            state=DISABLED)
        self._game_menu.add_command(
            label=ClientApplication.SET_PROGRAM_LABEL,
            command=self._set_program_callback,
            state=DISABLED)
        self._game_menu.add_command(
            label=ClientApplication.SET_STAR_PROGRAM_LABEL,
            command=self._set_star_program_callback,
            state=DISABLED)
        self._game_menu.add_command(
            label=ClientApplication.TIC_LABEL,
            command=self._tic_callback,
            state=DISABLED)
        self._game_menu.add_separator()
        self._game_menu.add_command(
            label=ClientApplication.QUIT_LABEL,
            command=self._quit_callback)

        menubar.add_command(label=ClientApplication.MENU_ABOUT_LABEL,
                            command=self._about_callback)

        global root
        root.config(menu=menubar)

    def _create_keyboard_shortcuts(self):
        self._game_menu.entryconfigure(ClientApplication.TIC_LABEL,
                                       accelerator="t")
        self.bind_all("<t>", lambda w: self._tic_callback())

    # callbacks ----------------------------------------------------------

    @log_on_enter('use case: new game', lvl='info')
    def _new_game_callback(self):
        if not self._ask_if_delete_current_game_if_exists():
            return

        map_filename = tkFileDialog.askopenfilename(
            title=ClientApplication.CHOOSE_MAP_FILE,
            filetypes=ClientApplication.MAP_FILE_TYPES,
            #initialdir=datafile_path('') # TODO
            parent=self,
        )
        if not map_filename:
            return

        directory = tkFileDialog.askdirectory(
            title=ClientApplication.CHOOSE_DIRECTORY_FOR_NEW_GAME,
            mustexist=True,
            parent=self,
        )
        if not directory:
            return

        try:
            stream = open(map_filename, 'r')
        except IOError as ex:
            self._warning(ClientApplication.TITLE_CREATE_NEW_GAME,
                          ClientApplication.CANNOT_CREATE_NEW_GAME + ' ' + \
                          ClientApplication.CANNOT_OPEN_FILE)
        else:
            try:
                game_map = load_game_map(stream.read())
            except InvalidGameMapData as ex:
                self._warning(ClientApplication.TITLE_CREATE_NEW_GAME,
                              ClientApplication.CANNOT_CREATE_NEW_GAME + ' ' + \
                              ClientApplication.MAP_FILE_IS_CORRUPTED)
            except IOError as ex:
                self._warning(ClientApplication.TITLE_CREATE_NEW_GAME,
                              ClientApplication.CANNOT_CREATE_NEW_GAME + ' ' + \
                              ClientApplication.IO_ERROR_DURING_READING)
            else:
                game = Game(game_map, DEFAULT_GAME_CONFIGURATION)
                system_configuration = DEFAULT_SYSTEM_CONFIGURATION
                game_session = GameSession(directory, system_configuration,
                                           game=game)
                self.set_game_session(game_session)
            finally:
                stream.close()

    @log_on_enter('use case: save game', mode='time', lvl='info')
    def _save_game_callback(self):
        try:
            self._game_session.save()
        except IOError as ex:
            log_exception()
            self._warning(ClientApplication.TITLE_SAVE_GAME,
                          ClientApplication.CANNOT_SAVE_GAME + ' ' + \
                          ClientApplication.IO_ERROR_DURING_SAVING)

    @log_on_enter('use case: load game', lvl='info')
    def _load_game_callback(self):
        if not self._ask_if_delete_current_game_if_exists():
            return

        directory = tkFileDialog.askdirectory(
            title=ClientApplication.TITLE_LOAD_GAME,
            mustexist=True,
            parent=self,
        )
        if directory is None:
            return

        try:
            game_session = GameSession(directory, DEFAULT_SYSTEM_CONFIGURATION)
        except IOError as ex:
            log_exception()
            self._warning(ClientApplication.TITLE_LOAD_GAME,
                          ClientApplication.CANNOT_LOAD_GAME + ' ' + \
                          ClientApplication.IO_ERROR_DURING_READING)
        except pickle.UnpicklingError as ex:
            log_exception()
            self._warning(ClientApplication.TITLE_LOAD_GAME,
                          ClientApplication.CANNOT_LOAD_GAME + ' ' + \
                          ClientApplication.MAP_FILE_IS_CORRUPTED)
        else:
            self.set_game_session(game_session)

    @log_on_enter('use case: add player', lvl='info')
    def _add_player_callback(self):
        name = tkSimpleDialog.askstring(
            title=ClientApplication.TITLE_CREATE_PLAYER,
            prompt=ClientApplication.ENTER_NEW_PLAYER_NAME,
            parent=self)
        if name is None:
            return

        color = self._reserve_color()
        try:
            self._game.new_player_with_units(name, color)
        except NoFreeStartPosition:
            self._warning(ClientApplication.CREATE_PLAYER,
                          ClientApplication.CANNOT_CREATE_PLAYER + ' ' + \
                          ClientApplication.NO_FREE_START_POSITION)
        else:
            self._set_game(self._game)

    @log_on_enter('use case: set program', lvl='info')
    def _set_program_callback(self):
        stream = tkFileDialog.askopenfile(
            title=ClientApplication.TITLE_CHOOSE_SOURCE_FILE,
            mode='r',
            parent=self)
        if stream is None:
            return

        filename = stream.name
        if filename.endswith('.cpp'):
            language = Language.CPP
        elif filename.endswith('.py'):
            language = Language.PYTHON
        else:
            self._warning(ClientApplication.TITLE_SET_PROGRAM,
                          ClientApplication.CANNOT_SET_PROGRAM + ' ' + \
                          ClientApplication.UNKNOWN_SOURCE_FILE_EXTENSION)
            return
        field = self._game.game_map[self._game_viewer.selection_position]
        unit = field.maybe_object
        program = Program(language=language, code=stream.read())
        self._game.set_program(unit, program)

    @log_on_enter('use case: set star program', lvl='info')
    def _set_star_program_callback(self):
        field = self._game.game_map[self._game_viewer.selection_position]
        unit = field.maybe_object
        self._game.set_program(unit, STAR_PROGRAM)

    @log_on_enter('use case: delete program', lvl='info')
    def _delete_program_callback(self):
        field = self._game.game_map[self._game_viewer.selection_position]
        unit = field.maybe_object
        self._game.set_program(unit, None)

    @log_on_enter('use case: tic', mode='time', lvl='info')
    def _tic_callback(self):
        self._game_session.tic()
        self._set_game(self._game_session.game)

    @log_on_enter('use case: quit', lvl='info')
    def _quit_callback(self):
        if not self._ask_if_quit_program():
            return

        global root
        root.destroy()

    @log_on_enter('use case: about game', lvl='info')
    def _about_callback(self):
        tkMessageBox.showinfo(
            title=ClientApplication.ABOUT_TITLE,
            message=ClientApplication.ABOUT_CONTENT,
            parent=self)

    def _field_select_callback(self, event):
        self._print_info_about_field_at(self._game_viewer.selection_position)
        self._refresh_game_menu_items_state()

    def _selection_removal_callback(self, event):
        self._refresh_game_menu_items_state()


    # other methods -------------------------------------------------------
    @log_on_enter('set game session')
    def set_game_session(self, game_session):
        self._game_session = game_session
        self._set_game(None)
        if game_session:
            self._set_game(game_session.game)

    def _set_game(self, game):
        """ Call it if game instance was changed and you want to make
        the application up to date."""
        if game is not None: # set game.free_colors
            if self._game is None or not hasattr(self._game, 'free_colors'):
                game.free_colors = \
                  list(ClientApplication.DEFAULT_PLAYER_COLORS)
            else:
                game.free_colors = self._game.free_colors
        self._game = game
        self._game_viewer.set_game(game)
        self._refresh_game_menu_items_state()

    def _reserve_color(self):
        if self._game.free_colors:
            return self._game.free_colors.pop()
        else:
            rand = lambda: random.randint(0, 255)
            return (rand(), rand(), rand())

    def _print_info_about_field_at(self, position):
        field = self._game.game_map[position]
        print "\nSelected position: (%d, %d)" % position
        print "Field: %s" % str(field)
        if isinstance(field.maybe_object, Unit):
            unit = field.maybe_object
            print "Unit: %s" % (unit,)
            print "Compilation: %s" % (unit.maybe_last_compilation_status,)
            print "Executing: %s" % (unit.maybe_run_status,)

    def _refresh_game_menu_items_state(self):
        has_game = self._game is not None
        obj = (self._game.game_map[self._game_viewer.selection_position].maybe_object
               if has_game and self._game_viewer.selection_position is not None
               else None)
        has_unit = (self._game is not None and
                    self._game_viewer.selection_position is not None and
                    isinstance(obj, Unit))

        state = NORMAL if has_game else DISABLED
        entries = [ClientApplication.ADD_PLAYER_LABEL,
                   ClientApplication.SAVE_GAME_LABEL,
                   ClientApplication.TIC_LABEL]
        for entry in entries:
            self._game_menu.entryconfigure(entry, state=state)

        state = NORMAL if has_unit else DISABLED
        entries = [ClientApplication.SET_PROGRAM_LABEL,
                   ClientApplication.SET_STAR_PROGRAM_LABEL,
                   ClientApplication.DELETE_PROGRAM_LABEL]
        for entry in entries:
            self._game_menu.entryconfigure(entry, state=state)

    def _warning(self, title, text):
        tkMessageBox.showwarning(title, text, parent=self)

    def _ask_if_delete_current_game_if_exists(self):
        if self._game:
            return tkMessageBox.askyesno(ClientApplication.TITLE_ARE_YOU_SURE,
                ClientApplication.WARNING_CURRENT_GAME_WILL_BE_LOST,
                icon=tkMessageBox.WARNING,
                parent=self
            )
        else:
            return True

    def _ask_if_quit_program(self):
        return tkMessageBox.askyesno(
            ClientApplication.TITLE_QUIT_PROGRAM,
            ClientApplication.QUIT_PROGRAM_QUESTION,
            icon=tkMessageBox.WARNING,
            parent=self
        )


def run():
    # prevent "errors occured" message box in py2exe distribution
    turn_off_standard_streams_if_it_is_py2exe_distribution()

    global root, app
    init_logging('debug')
    try:
        root = Tk()
        root.report_callback_exception = log_error_callback
        app = ClientApplication(master=root)
        app.mainloop()
    except Exception as ex:
        log_exception('Unhandled exception outside tkinter!')
    finally:
        shutdown_logging()

if __name__ == "__main__":
    run()
