#!/usr/bin/env python
#-*- coding:utf-8 -*-

try:
    import cPickle as pickle
except:
    import pickle
import itertools
import math
import os.path
from Tkinter import *
import tkColorChooser
import tkFileDialog
import tkFont
import tkMessageBox
import tkSimpleDialog
from PIL import Image, ImageTk # it overrides Tkinter.Image so it must be after Tkinter import statement

from scriptcraft import direction
from scriptcraft.gamemap import GameMap, NoFreeStartPosition
from scriptcraft.gamestate import (actions, Game, DEFAULT_GAME_CONFIGURATION,
                                   Language, Program, STAR_PROGRAM)
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

    SCROLLING_SENSITIVITY = 1.05 # in (1, +inf); greater means faster scrolling

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
        self._zoom = 0.25
        self._delta = (0.0, 0.0)
        self._game = None
        self._scaled_images_cache = {}
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
            self._draw_game(game)
            self._set_selection_position(self.selection_position)

    def _draw_game(self, game):
        def draw_arrow_from_to(source, destination):
            delta = map(lambda (a, b): a-b, zip(destination,
                                                source))
            d = direction.FROM_RAY[tuple(delta)]
            direction_name = direction.TO_FULL_NAME[d]
            self._draw('arrow-%s' % direction_name, source,
                        extra_tags=['upper-layer'])

        # go from west to east and in each row from north to south
        for position in itertools.product(xrange(game.game_map.size[0]),
                                          xrange(game.game_map.size[1])):
            field = game.game_map.get_field(position)
            self._draw('flat_field', position) # draw ground
            if field.has_mineral_deposit(): # draw minerals
                self._draw('minerals', position)
            if field.has_trees(): # draw trees
                self._draw('tree', position)

            if field.has_unit(): # draw unit
                unit = game.units_by_IDs[field.get_unit_ID()]
                switch = {'4': lambda u: 'base',
                          '6': lambda u: 'tank',
                          '5': lambda u: ('full_miner'
                                          if u.minerals
                                          else 'empty_miner')}
                sprite_name = switch[unit.type.main_name](unit)
                self._draw(sprite_name, position)

                x, y = self._to_screen_coordinate(position)
                color = '#' + "%02x%02x%02x" % unit.player.color
                font = self._get_font_for_current_zoom()
                self.create_text(x, y, fill=color, text=unit.player.name,
                                 font=font, tags=['text'],
                                 state=NORMAL if font else HIDDEN)

                if isinstance(unit.action, actions.GatherAction):
                    draw_arrow_from_to(unit.position, unit.action.source)
                elif isinstance(unit.action, actions.StoreAction):
                    destination_unit = self._game.units_by_IDs[
                        unit.action.storage_ID]
                    destination = destination_unit.position
                    draw_arrow_from_to(unit.position, destination)
                elif isinstance(unit.action, actions.MoveAction):
                    draw_arrow_from_to(unit.action.source,
                                       unit.action.destination)
                elif isinstance(unit.action, actions.FireAction):
                    self._draw('fire', unit.action.destination,
                               extra_tags=['upper-layer'])

        self.tag_raise('upper-layer')

    def _set_selection_position(self, new_position):
        """ Create or move exisitng pointer. Argument new_position can
        be None if you want to disable the pointer. """

        self.delete('selection')
        state = HIDDEN if new_position is None else NORMAL
        self._draw('pointer', new_position or (0, 0),
                   state=state, extra_tags=['selection'])
        self.selection_position = new_position

    def _draw(self, name, position, state=NORMAL, extra_tags=None):
        """ Draw sprite with name 'name' at position 'position' in
        game coordinates."""

        extra_tags = extra_tags or []
        position = self._to_screen_coordinate(position)
        x, y = self._to_image_position(position)
        image = self._get_scaled_sprite(name)
        self.create_image(x, y, image=image, anchor=NW,
                          state=state, tags=[name]+extra_tags)

    def _get_font_for_current_zoom(self):
        size = int(40*self._zoom)
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

    def _get_scaled_sprite(self, name):
        """ Return (PIL.)ImageTk scaled by self._zoom factor. """

        # if cached, return cached value
        image = self._scaled_images_cache.get(name, None)
        if image:
            return image

        # otherwise compute, cache and return
        image = self._get_image(name)
        width, height = 256, 288
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
        return (128*self._zoom*(x-y-2*self._delta[0]),
                72*self._zoom*(x+y-2*self._delta[1]))

    def _to_game_coordinate(self, (x, y)):
        """ From screen coordinates. """
        return (x/256.0/self._zoom + y/144.0/self._zoom \
                + self._delta[0] + self._delta[1],
                -x/256.0/self._zoom + y/144.0/self._zoom \
                - self._delta[0] + self._delta[1])

    def _to_image_position(self, (x, y)):
        """ From screen coordinaties. """
        return x-128*self._zoom, y-144*self._zoom

    @log_on_enter('setting zoom in game viewer', mode='only time')
    def _set_zoom(self, zoom, (XS, YS)):
        """ Set zoom. The point (XS, YS) in screen coordinate doesn't
        move."""

        # It clears cache of scaled images. Due to reference count bug
        # all images will be removed from memory!

        # compute new self._delta and self._zoom
        xS, yS = self._to_game_coordinate((XS, YS))
        self._delta = [-XS/256.0/zoom + xS/2.0 - yS/2.0,
                       -YS/144.0/zoom + xS/2.0 + yS/2.0]
        self._zoom, old_zoom = zoom, self._zoom

        # scale all images
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
                self._delta = (self._delta[0]-dx/256.0/self._zoom,
                           self._delta[1]-dy/144.0/self._zoom)

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
            if self._game.game_map.is_valid_position(integer_click_position):
                self._set_selection_position(integer_click_position)
                self.event_generate("<<field-selected>>")
            elif self.selection_position:
                self._set_selection_position(None)
                self.event_generate("<<selection-removed>>")



DEFAULT_SYSTEM_CONFIGURATION = SystemConfiguration()


class ClientApplication(Frame):

    MENU_GAME_LABEL = "Game"
    NEW_GAME_LABEL = "New game"
    SAVE_GAME_LABEL = "Save game"
    LOAD_GAME_LABEL = "Load game"
    ADD_PLAYER_LABEL = "Add player"
    SET_PROGRAM_LABEL = "Set program"
    SET_STAR_PROGRAM_LABEL = "Set star program"
    DELETE_PROGRAM_LABEL = "Delete program"
    TIC_LABEL = "One turn in game"
    QUIT_LABEL = "Quit"

    MAP_FILETYPES = [
        ('Scriptcraft map', '*.map'),
        ('All files', '*'),]
    GAME_FILETYPES = [
        ('Scriptcraft game', '*.game'),
        ('All files', '*'),]

    # initializing --------------------------------------------------------

    def __init__(self, master):
        Frame.__init__(self, master)
        self._init_gui()
        self._game = None
        self._game_session = None
        self._load_testing_game()

    @log_on_enter('load game for testing')
    def _load_testing_game(self):
        filename = datafile_path('maps/default.map')
        game_map = pickle.load(open(filename, 'r'))
        game = Game(game_map, DEFAULT_GAME_CONFIGURATION)
        session = GameSession(
            directory='scriptcraft/.tmp',
            system_configuration=DEFAULT_SYSTEM_CONFIGURATION,
            game=game)
        game.new_player_with_units('Bob', (255, 0, 0))
        game.new_player_with_units('Alice', (255, 255, 0))

        def set_program(unit_id, filename):
            program = Program(Language.PYTHON,
                              open('scriptcraft/.tmp/'+filename).read())
            game.set_program(game.units_by_IDs[unit_id], program)
        for i in xrange(3,7):
            set_program(i, 'gather.py')
        for i in xrange(9,13):
            set_program(i, 'gather_Alice.py')

        self.set_game_session(session)

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

        directory = tkFileDialog.askdirectory(
            title="Choose directory for new game",
            mustexist=True,
            parent=self,
        )
        if not directory:
            return

        try:
            filename = datafile_path('maps/default.map')
            stream = open(filename, 'r')
            game_map = pickle.load(stream)
        except pickle.UnpicklingError as ex:
            self._warning('Create new game',
                'Cannot create new game - map file is corrupted.')
        except IOError as ex:
            self._warning('Create new game',
                'Cannot create new game - io error.')
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
            self._warning('Save game',
                'Cannot save game - io error.')

    @log_on_enter('use case: load game', lvl='info')
    def _load_game_callback(self):
        if not self._ask_if_delete_current_game_if_exists():
            return

        directory = tkFileDialog.askdirectory(
            title='Load game',
            mustexist=True,
            parent=self,
        )
        if directory is None:
            return

        try:
            game_session = GameSession(directory, DEFAULT_SYSTEM_CONFIGURATION)
        except IOError as ex:
            self._warning('Load game',
                'Cannot load game - io error.')
        except pickle.UnpicklingError as ex:
            self._warning('Load game',
                'Cannot load game - corrupted game file.')
        else:
            self.set_game_session(game_session)

    @log_on_enter('use case: add player', lvl='info')
    def _add_player_callback(self):
        name = tkSimpleDialog.askstring(
            title='Create player',
            prompt='Enter new player name',
            parent=self)
        if name is None:
            return

        color = tkColorChooser.askcolor(
            title='Create player - choose color for new player',
            parent=self)
        if color is None:
            return
        color = color[0] # original color was ((r, g, b), "#rrggbb")

        try:
            self._game.new_player_with_units(name, color)
        except NoFreeStartPosition:
            self._warning('Create player',
                'Cannot create player - no free start position on map.')
        else:
            self._set_game(self._game)

    @log_on_enter('use case: set program', lvl='info')
    def _set_program_callback(self):
        stream = tkFileDialog.askopenfile(
            title='Choose source file',
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
            self._warning('Set program',
                'Cannot set program - unknown source file extension.')
            return
        field = self._game.game_map.get_field(self._game_viewer.selection_position)
        unit = self._game.units_by_IDs[field.get_unit_ID()]
        program = Program(language=language, code=stream.read())
        self._game.set_program(unit, program)

    @log_on_enter('use case: set star program', lvl='info')
    def _set_star_program_callback(self):
        field = self._game.game_map.get_field(self._game_viewer.selection_position)
        unit = self._game.units_by_IDs[field.get_unit_ID()]
        self._game.set_program(unit, STAR_PROGRAM)

    @log_on_enter('use case: delete program', lvl='info')
    def _delete_program_callback(self):
        field = self._game.game_map.get_field(self._game_viewer.selection_position)
        unit = self._game.units_by_IDs[field.get_unit_ID()]
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
        self._game = game
        self._game_viewer.set_game(game)
        self._refresh_game_menu_items_state()

    def _print_info_about_field_at(self, position):
        field = self._game.game_map.get_field(position)
        print "\nSelected position: (%d, %d)" % position
        print "Field: %s" % str(field)
        if field.has_unit():
            unit = self._game.units_by_IDs[field.get_unit_ID()]
            print "Unit: %s" % (unit,)
            print "Compilation: %s" % (unit.maybe_last_compilation_status,)
            print "Executing: %s" % (unit.maybe_run_status,)

    def _refresh_game_menu_items_state(self):
        has_game = self._game is not None
        has_unit = (self._game is not None and
                    self._game_viewer.selection_position is not None and
                    self._game.game_map.get_field(
                        self._game_viewer.selection_position
                    ).has_unit())

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
            return tkMessageBox.askyesno(
                'Are you sure?',
                'Are you sure? Current game will be lost.',
                icon=tkMessageBox.WARNING,
                parent=self
            )
        else:
            return True

    def _ask_if_quit_program(self):
        return tkMessageBox.askyesno(
            'Quit program.',
            'Do you really want to quit the program?',
            icon=tkMessageBox.WARNING,
            parent=self
        )


def run():
    global root, app
    init_logging('debug')
    root = Tk()
    root.report_callback_exception = log_error_callback
    app = ClientApplication(master=root)
    app.mainloop()
    shutdown_logging()

if __name__ == "__main__":
    run()
