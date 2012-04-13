#!/usr/bin/env python
#-*- coding:utf-8 -*-

#import time
from Tkinter import *
import tkColorChooser
import tkFileDialog
import tkMessageBox
import tkSimpleDialog
from PIL import Image, ImageTk # it overrides Tkinter.Image so it must be after Tkinter import statement

try:
    import cPickle as pickle
except:
    import pickle

from scriptcraft.core.Game import Game
from scriptcraft.core.GameConfiguration import DEFAULT_GAME_CONFIGURATION
from scriptcraft.core.GameMap import GameMap, NoFreeStartPosition
from tests.core.Game import BaseGameTestCase
from scriptcraft.utils import *



class GameViewer(Canvas):

    SCROLLING_SENSITIVITY = 1.05 # in (1, +inf); greater means faster scrolling

    def __init__(self, master):
        Canvas.__init__(self, master, width=800, height=600, bg='yellow')
        self.pack(expand=YES, fill=BOTH)

        # bindings
        self.bind('<B1-Motion>', self._move_event)
        self.bind('<ButtonRelease-1>', self._release_event)
        self.bind('<MouseWheel>', self._roll_wheel_event)
        self.bind('<Button-4>', self._roll_wheel_event)
        self.bind('<Button-5>', self._roll_wheel_event)
        self.bind('<Button-1>', self._click_event)

        # own attributes
        self.zoom = 0.25
        self.delta = (0.0, 0.0)
        self.game = None
        self._scaled_images_cache = {}
        self.pointer_position = None # None or (x, y)

    def set_game(self, game):
        """ In this method game instance passed during previous call
        is used. The previous game instance cannot be modified since
        the previous call! """
        previous_game = self.game
        self.game = game

        if previous_game:
            self.delete(ALL)

        if not game:
            pass

        else:
            self.set_pointer_position(self.pointer_position)

            def draw(sprite_name):
                image = self._get_scaled_sprite(sprite_name)
                self.create_image(x, y, image=image,
                                  anchor=NW, tags=[sprite_name])

            for i in xrange(0, game.game_map.size[0]):
                for j in xrange(0, game.game_map.size[1]):
                    field = game.game_map.get_field((i, j))
                    x, y = self._to_screen_coordinate((i, j))
                    x, y = x-128*self.zoom, y-144*self.zoom

                    # ground
                    draw('flat_field')

                    # minerals
                    if field.has_mineral_deposit():
                        draw('minerals')

                    # trees
                    if field.has_trees():
                        draw('tree')

                    # unit
                    if field.has_unit():
                        unit = game.units_by_IDs[field.get_unit_ID()]
                        type_name = unit.type.main_name
                        if type_name == '4': # base
                            draw('base')
                        elif type_name == '6': # tank
                            draw('tank')
                        elif type_name == '5': # miner
                            if unit.minerals:
                                draw('full_miner')
                            else:
                                draw('empty_miner')

    def set_pointer_position(self, new_position):
        """ Create or move exisitng pointer. Argument new_position can
        be None if you want to disable the pointer. """

        self.delete('pointer')
        image = self._get_scaled_sprite('pointer')
        x, y = self._to_screen_coordinate(new_position or (0, 0))
        x, y = self._to_image_position((x, y))
        state = HIDDEN if new_position is None else NORMAL
        self.create_image(x, y, image=image,
                          anchor=NW, tags=['pointer'],
                          state=state)
        self.pointer_position = new_position

    def print_info_about_field_under_pointer(self):
        field = self.game.game_map.get_field(self.pointer_position)
        print "\nField: %s" % str(field)
        if field.has_unit():
            unit = self.game.units_by_IDs[field.get_unit_ID()]
            print "Unit: %s" % unit
            print "Compilation: %s" % unit.maybe_last_compilation_status
            print "Executing: %s" % unit.maybe_run_status
            print "Program: %s" % unit.program

    @memoized
    def _get_image(self, name):
        """ Return (PIL.)Image instance. """
        path = '../graphic/%s.png' % name
        image = Image.open(path)
        return image

    def _get_scaled_sprite(self, name):
        """ Return (PIL.)ImageTk scaled by self.zoom factor. """
        # if cached, return cached value
        image = self._scaled_images_cache.get(name, None)
        if image:
            return image

        # otherwise compute, cache and return
        image = self._get_image(name)
        width, height = 256, 288
        new_width, new_height = width*self.zoom+2, height*self.zoom+2
        image = image.resize((new_width, new_height), Image.NEAREST)
        image = ImageTk.PhotoImage(image)

        # no problem with bug connected with reference count --
        # caching keeps image reference
        self._scaled_images_cache[name] = image
        return image

    def _to_screen_coordinate(self, (x, y)):
        """ From game coordinates. """
        return (128*self.zoom*(x-y-2*self.delta[0]),
                72*self.zoom*(x+y-2*self.delta[1]))

    def _to_game_coordinate(self, (x, y)):
        """ From screen coordinates. """
        return (x/256.0/self.zoom + y/144.0/self.zoom + self.delta[0] + self.delta[1],
                -x/256.0/self.zoom + y/144.0/self.zoom - self.delta[0] + self.delta[1])

    def _to_image_position(self, (x, y)):
        """ From screen coordinaties. """
        return x-128*self.zoom, y-144*self.zoom

    def _roll_wheel_event(self, event):
        if self.game:
            # respond to Linux or Windows wheel event
            delta = 0
            if event.num == 5 or event.delta == -120:
                delta -= 1
            if event.num == 4 or event.delta == 120:
                delta += 1

            factor = GameViewer.SCROLLING_SENSITIVITY**delta
            self._set_zoom(self.zoom*factor, (event.x, event.y))
            #self._clear_scaled_images_cache()
            self.scale(ALL, event.x, event.y, factor, factor)

    def _set_zoom(self, zoom, (XS, YS)):
        """ Set zoom. The point (XS, YS) in screen coordinate doesn't move.

        It clears cache of scaled images. Due to reference count bug
        all images will be removed from memory! """
        xS, yS = self._to_game_coordinate((XS, YS))
        self.delta = [-XS/256.0/zoom + xS/2.0 - yS/2.0,
                      -YS/144.0/zoom + xS/2.0 + yS/2.0]
        self.zoom = zoom

        # scale all images
        names = self._scaled_images_cache.keys()
        self._scaled_images_cache = {} # clear cache
        for name in names:
            image = self._get_scaled_sprite(name)
            self.itemconfigure(name, image=image)

    def _move_event(self, event):
        if self.game:
            if not hasattr(self, '_last_pos'):
                self._last_pos = (event.x, event.y)
                return

            dx, dy = event.x - self._last_pos[0], event.y - self._last_pos[1]
            self._last_pos = (event.x, event.y)
            self.move(ALL, dx, dy)
            self.delta = (self.delta[0]-dx/256.0/self.zoom,
                          self.delta[1]-dy/144.0/self.zoom)

    def _release_event(self, event):
        if hasattr(self, '_last_pos'):
            del self._last_pos

        if hasattr(self, '_clicked_position'):
            release_position = (event.x, event.y)
            if self._clicked_position == release_position:
                self._single_click_event(event)

    def _click_event(self, event):
        if self.game:
            self._clicked_position = (event.x, event.y)

    def _single_click_event(self, event):
        if self.game:
            click_position = self._to_game_coordinate((event.x, event.y))
            click_position = map(int, click_position)
            if self.game.game_map.is_valid_position(click_position):
                self.set_pointer_position(click_position)
                self.print_info_about_field_under_pointer()
            else:
                self.set_pointer_position(None)


class ClientApplication(Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        self._init_gui()
        #self._load_default_map()

    def _load_default_map(self):
        stream = open('../maps/default.map', 'r')
        game_map = pickle.load(stream)
        stream.close()
        game = Game(game_map, DEFAULT_GAME_CONFIGURATION)
        self.set_game(game)

    def set_game(self, game):
        self._game = game
        self._game_viewer.set_game(game)

    def _init_gui(self):
        self.pack(expand=YES, fill=BOTH)
        self._create_menubar()
        self._game_viewer = GameViewer(self)

    def _create_menubar(self):
        menubar = Menu(self)

        game_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Game', menu=game_menu)
        game_menu.add_command(label="New game",
                              command=self._new_game_callback)
        game_menu.add_separator()
        game_menu.add_command(label="Add player",
                              command=self._add_player_callback)
        game_menu.add_command(label="Tic",
                              command=self._tic_callback)
        game_menu.add_separator()
        game_menu.add_command(label="Quit",
                              command=self._quit_callback)

        global root
        root.config(menu=menubar)

    def _new_game_callback(self):
        filetypes = [
            ('Scriptcraft map', '*.map'),
            ('All files', '*'),
        ]
        stream = tkFileDialog.askopenfile(
            title='Choose map file',
            mode='r',
            filetypes=filetypes,
            parent=self
        )
        if stream is None:
            return

        try:
            game_map = pickle.load(stream)
        except pickle.UnpicklingError as ex:
            tkMessageBox.showwarning(
                'Create new game',
                'Cannot create new game - map file is corrupted.',
                parent=self
            )
            return
        except IOError as ex:
            tkMessageBox.showwarning(
                'Create new game',
                'Cannot create new game - io error.',
                parent=self
            )
            return
        finally:
            stream.close()

        # we will create game
        game = Game(game_map, DEFAULT_GAME_CONFIGURATION)
        self.set_game(game)

    def _add_player_callback(self):
        name = tkSimpleDialog.askstring(
            title='Create player',
            prompt='Enter new player name',
            parent=self
        )
        if name is None:
            return

        color = tkColorChooser.askcolor(
            title='Create player - choose color for new player',
            parent=self
        )
        if color is None:
            return

        try:
            self._game.new_player_with_units(name, color)
        except NoFreeStartPosition:
            tkMessageBox.showwarning(
                'Create player',
                'Cannot create player - no free start position on map.',
                parent=self,
            )

        self.set_game(self._game)

    def _tic_callback(self):
        self._game.tic('tmp')
        self.set_game(self._game)

    def _quit_callback(self):
        global root
        root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = ClientApplication(master=root)
    app.mainloop()
    root.destroy()
