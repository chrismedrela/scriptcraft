#!/usr/bin/env python
#-*- coding:utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk
import math
import time
import re
import os

from scriptcraft.core.Game import Game
from scriptcraft.core.GameMap import GameMap
from tests.core.Game import BaseGameTestCase
from scriptcraft.utils import *



class GameViewer(gtk.DrawingArea):
    def __init__(self):
        super(GameViewer, self).__init__()

        self.set_size_request(800, 600)
        self.connect("motion-notify-event", self._motion_event)
        self.connect("scroll-event", self._scroll_event)
        self.connect("expose-event", self._expose_callback)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.MOTION_NOTIFY |
                        gtk.gdk.POINTER_MOTION_MASK)
        self.show()

        self.zoom = 0.25
        self.delta = [-0.25, -0.25]

        self.scaled_sprite_cache = {}
        self._game = None

    def set_game(self, game):
        """
        Set Game or None. The game wont be modified but it will be
        read so you shouldnt modify this game.
        """
        self._game = game

    def _expose_callback(self, area, event):
        context = self.window.cairo_create()

        if not self._game:
            return True

        def draw_pixbuf((x, y), pixbuf):
            X, Y = self.to_screen_coordinate((x, y))
            X -= 128*self.zoom
            Y -= 144*self.zoom
            context.set_source_pixbuf(pixbuf, X, Y)
            context.paint()

        width, height = self.allocation.width, self.allocation.height
        x_min = max(int(math.floor(self.to_game_coordinate((0, 0))[0])), 0)
        x_max = min(int(math.ceil(self.to_game_coordinate((width, height))[0])), self._game.game_map.size[0]-1)
        y_min = max(int(math.floor(self.to_game_coordinate((width, 0))[1])), 0)
        y_max = min(int(math.ceil(self.to_game_coordinate((0, height))[1])), self._game.game_map.size[1]-1)

        for x in xrange(x_min, x_max+1):
            for y in xrange(y_min, y_max+1):
                field = self._game.game_map.get_field((x, y))

                # ground
                draw_pixbuf((x, y), self._get_scaled_sprite('flat_field'))

                # minerals
                if field.has_mineral_deposit():
                    draw_pixbuf((x, y), self._get_scaled_sprite('minerals'))

                # trees
                if field.has_trees():
                    draw_pixbuf((x, y), self._get_scaled_sprite('tree'))

                # unit
                if field.has_unit():
                    unit = self._game.units_by_IDs[field.get_unit_ID()]
                    type_name = unit.type.main_name
                    if type_name == '4': # base
                        draw_pixbuf((x, y), self._get_scaled_sprite('base'))
                    elif type_name == '6': # tank
                        draw_pixbuf((x, y), self._get_scaled_sprite('tank'))
                    elif type_name == '5': # miner
                        if unit.minerals:
                            draw_pixbuf((x, y), self._get_scaled_sprite('full_miner'))
                        else:
                            draw_pixbuf((x, y), self._get_scaled_sprite('empty_miner'))

        return True

    def _scroll_event(self, area, event):
        if not self._game:
            return

        WSP = 1.1
        if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_DOWN):
            zoom = self.zoom * (WSP if event.direction == gtk.gdk.SCROLL_UP else 1/WSP)
            point = event.x, event.y
            self.set_zoom(zoom, point)
            self.queue_draw()

    def _motion_event(self, area, event):
        if not self._game:
            return

        if hasattr(self, 'last_mouse_position'):
            if event.state & gtk.gdk.BUTTON3_MASK:
                dx = self.last_mouse_position[0] - event.x
                dy = self.last_mouse_position[1] - event.y
                self.delta[0] += float(dx)/self.zoom/256
                self.delta[1] += float(dy)/self.zoom/144
                self.queue_draw()

        self.last_mouse_position = (event.x, event.y)

    def to_screen_coordinate(self, (x, y)):
        return (128*self.zoom*(x-y-2*self.delta[0]),
                72*self.zoom*(x+y-2*self.delta[1]))

    def to_game_coordinate(self, (x, y)):
        return (x/256.0/self.zoom + y/144.0/self.zoom + self.delta[0] + self.delta[1],
                -x/256.0/self.zoom + y/144.0/self.zoom - self.delta[0] + self.delta[1])

    def set_zoom(self, zoom, (XS, YS)):
        """ Set zoom. The point (XS, YS) in screen coordinate doesn't move. """
        xS, yS = self.to_game_coordinate((XS, YS))
        self.delta = [-XS/256.0/zoom + xS/2.0 - yS/2.0,
                      -YS/144.0/zoom + xS/2.0 + yS/2.0]
        self.zoom = zoom
        self.scaled_sprite_cache = {}

    @ memoized
    def _get_sprite(self, name):
        pixbuf = gtk.gdk.pixbuf_new_from_file("../graphic/%s.png" % name)
        return pixbuf

    def _get_scaled_sprite(self, name):
        # if cached, return cached value
        id = (name, self.zoom)
        sprite = self.scaled_sprite_cache.get(id, None)
        if sprite:
            return sprite

        # otherwise compute, save in cache and return
        sprite = self._get_sprite(name)
        new_width = int(sprite.get_width()*self.zoom)+2
        new_height = int(sprite.get_height()*self.zoom)+2
        scaled = sprite.scale_simple(new_width, new_height, gtk.gdk.INTERP_BILINEAR)
        self.scaled_sprite_cache[id] = scaled
        return scaled

        """
        gtk.gdk.INTERP_NEAREST    Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
        gtk.gdk.INTERP_TILES    This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
        gtk.gdk.INTERP_BILINEAR    Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
        gtk.gdk.INTERP_HYPER
        """


class HelloWorld(object):

    def __init__(self):
        self._build_GUI()
        self.window.show()

        # set game
        b = BaseGameTestCase(methodName='__init__')
        b.setUp()
        self.area.set_game(b.game)

    def main(self):
        gtk.main()

    def quit(self):
        """ Called when a user click 'quit' option or close the window. """
        gtk.main_quit()

    def _build_GUI(self):
        self._prebuild_window()
        self._build_area()
        self._build_menu_bar()
        self._build_window()
        self.window.show()

    def _build_area(self):
        self.area = GameViewer()
        self.area.show()

    def _build_menu_bar(self):
        self._build_game_menu()
        self.menu_bar = gtk.MenuBar()
        self.menu_bar.append(self.menu_game_item)
        self.menu_bar.show()

    def _build_game_menu(self):
        self.menu_game_item = gtk.MenuItem("Game")
        self.menu_game = gtk.Menu()
        self.menu_game_item.set_submenu(self.menu_game)

        self._build_quit_button()
        #items = [(gtk.MenuItem("New game"), lambda *args: f(args)),
        #         (gtk.MenuItem("Open game"), lambda *args: f(args)),
        #         (gtk.MenuItem("Save game"), lambda *args: f(args)),
        #         (gtk.MenuItem("Add player"), lambda *args: f(args)),
        #         (gtk.MenuItem("Tic"), lambda *args: f(args)),
        #         (gtk.MenuItem("Quit"), lambda *args: f(args)),]
        #map(lambda (i, f): i.connect("activate", f), items)
        #map(lambda (i, f): menu_game.append(i), items)
        #map(lambda (i, f): i.show(), items)

        self.menu_game_item.show()

    def _build_quit_button(self):
        quit_item = gtk.MenuItem("_Quit")
        quit_item.connect_object("activate", gtk.Widget.destroy, self.window)
        self.menu_game.append(quit_item)
        quit_item.show()

    def _prebuild_window(self):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    def _build_window(self):
        self.window.set_title("First tests")
        self.window.connect("destroy", lambda widget: self.quit())

        vbox = gtk.VBox(False, 0)
        self.window.add(vbox)
        vbox.show()
        vbox.pack_start(self.menu_bar, False, False, 2)
        vbox.pack_end(self.area, True, True, 2)


if __name__ == "__main__":
    hello = HelloWorld()
    hello.main()
