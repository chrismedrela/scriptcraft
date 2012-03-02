#!/usr/bin/env python
#-*- coding:utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk
import math

from scriptcraft.utils import *



class GameViewer(gtk.DrawingArea):
    def __init__(self):
        super(GameViewer, self).__init__()

        self.set_size_request(800, 600)
        self.connect("motion-notify-event", self.motion_event)
        self.connect("scroll-event", self.scroll_event)
        self.connect("expose-event", self.expose_callback)
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.MOTION_NOTIFY |
                        gtk.gdk.POINTER_MOTION_MASK)
        self.show()

        self.zoom = 0.05
        self.delta = [-0.25, -0.25]

        self.scaled_sprite_cache = {}

    def expose_callback(self, area, event):
        self.context = self.window.cairo_create()
        self.context.rectangle(event.area.x, event.area.y,
                               event.area.width, event.area.height)
        self.context.clip()

        self.my_draw(self.context)
        return False

        style = self.get_style()
        gc = style.fg_gc[gtk.STATE_NORMAL]

        self.pixbuf = self.get_scaled_sprite('flat_field', self.zoom)
        self.pixbuf2 = self.get_scaled_sprite('minerals', self.zoom)

        """
        gtk.gdk.INTERP_NEAREST    Nearest neighbor sampling; this is the fastest and lowest quality mode. Quality is normally unacceptable when scaling down, but may be OK when scaling up.
        gtk.gdk.INTERP_TILES    This is an accurate simulation of the PostScript image operator without any interpolation enabled. Each pixel is rendered as a tiny parallelogram of solid color, the edges of which are implemented with antialiasing. It resembles nearest neighbor for enlargement, and bilinear for reduction.
        gtk.gdk.INTERP_BILINEAR    Best quality/speed balance; use this mode by default. Bilinear interpolation. For enlargement, it is equivalent to point-sampling the ideal bilinear-interpolated image. For reduction, it is equivalent to laying down small tiles and integrating over the coverage area.
        gtk.gdk.INTERP_HYPER
        """

        def draw((x, y), pixbuf):
            X, Y = self.to_screen_coordinate((x, y))
            X -= 128*self.zoom
            Y -= 144*self.zoom
            rect = self.allocation
            if (X <= rect.width and Y <= rect.height and
                X > -pixbuf.get_width() and Y > -pixbuf.get_height()):
                self.window.draw_pixbuf(gc, self.pixbuf, 0, 0, X, Y)
                self.window.draw_pixbuf(gc, self.pixbuf2, 0, 0, X, Y)

        width, height = self.allocation.width, self.allocation.height
        x_min = int(math.floor(self.to_game_coordinate((0, 0))[0]))
        x_max = int(math.ceil(self.to_game_coordinate((width, height))[0]))
        y_min = int(math.floor(self.to_game_coordinate((width, 0))[1]))
        y_max = int(math.ceil(self.to_game_coordinate((0, height))[1]))

        for x in xrange(x_min, x_max+1):
            for y in xrange(y_min, y_max+1):
                draw((x, y), self.pixbuf)

        return True

    def scroll_event(self, area, event):
        WSP = 1.1
        if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_DOWN):
            zoom = self.zoom * (WSP if event.direction == gtk.gdk.SCROLL_UP else 1/WSP)
            point = event.x, event.y
            self.set_zoom(zoom, point)
            self.queue_draw()

    def motion_event(self, area, event):
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
    def get_sprite(self, name):
        pixbuf = gtk.gdk.pixbuf_new_from_file("../graphic/%s.png" % name)
        return pixbuf

    def get_scaled_sprite(self, name, scale):
        # if cached, return cached value
        id = (name, scale)
        sprite = self.scaled_sprite_cache.get(id, None)
        if sprite:
            return sprite

        # otherwise compute, save in cache and return
        sprite = self.get_sprite(name)
        new_width = int(sprite.get_width()*scale)+2
        new_height = int(sprite.get_height()*scale)+2
        scaled = sprite.scale_simple(new_width, new_height, gtk.gdk.INTERP_BILINEAR)
        self.scaled_sprite_cache[id] = scaled
        return scaled


class ClientWindow(gtk.Window):
    def __init__(self):
        super(ClientWindow, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_title("First tests")
        self.connect("destroy", lambda widget: gtk.main_quit())


class HelloWorld(object):
    def __init__(self):
        self.area = GameViewer()
        self.area.show()
        self.window = ClientWindow()
        self.window.add(self.area)
        self.window.show()

    def main(self):
        gtk.main()


if __name__ == "__main__":
    hello = HelloWorld()
    hello.main()