#!/usr/bin/env python
#-*- coding:utf-8 -*-

#import time
from Tkinter import *
from PIL import Image, ImageTk # it overrides Tkinter.Image so it must be after Tkinter import statement

try:
    import cPickle as pickle
except:
    import pickle

from scriptcraft.core.Game import Game
from scriptcraft.core.GameConfiguration import DEFAULT_GAME_CONFIGURATION
from scriptcraft.core.GameMap import GameMap
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

        # own attributes
        self.zoom = 1.0
        self.delta = (0.0, 0.0)
        self.game = None
        self._scaled_images_cache = {}

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
                        unit = self._game.units_by_IDs[field.get_unit_ID()]
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
        return (128*self.zoom*(x-y-2*self.delta[0]),
                72*self.zoom*(x+y-2*self.delta[1]))

    def _to_game_coordinate(self, (x, y)):
        return (x/256.0/self.zoom + y/144.0/self.zoom + self.delta[0] + self.delta[1],
                -x/256.0/self.zoom + y/144.0/self.zoom - self.delta[0] + self.delta[1])

    def _roll_wheel_event(self, event):
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


class ClientApplication(Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        self._init_gui()

        try:
            stream = open('../maps/default.map', 'r')
            game_map = pickle.load(stream)
        except (pickle.UnpicklingError, IOError) as ex:
            print 'zonk'
            return
        finally:
            stream.close()

        # we will create game
        game = Game(game_map, DEFAULT_GAME_CONFIGURATION)
        self._game_viewer.set_game(game)

    def _init_gui(self):
        self.pack(expand=YES, fill=BOTH)
        self._create_menubar()
        self._game_viewer = GameViewer(self)

    def _create_menubar(self):
        menubar = Menu(self)

        game_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Game', menu=game_menu)
        game_menu.add_command(label="Add player",
                         command=self._add_player_callback)
        game_menu.add_separator()
        game_menu.add_command(label="Quit",
                         command=self._quit_callback)

        global root
        root.config(menu=menubar)

    def _add_player_callback(self):
        pass

    def _quit_callback(self):
        global root
        root.destroy()


if __name__ == "__main__":
    root = Tk()
    app = ClientApplication(master=root)
    app.mainloop()
    root.destroy()
