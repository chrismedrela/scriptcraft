#!/usr/bin/env python
#-*- coding:utf-8 -*-

#import time
from Tkinter import *
from PIL import Image, ImageTk # it overrides Tkinter.Image so it must be after Tkinter import statement

#try:
#    import cPickle as pickle
#except:
#    import pickle

from scriptcraft.core.Game import Game
from scriptcraft.core.GameConfiguration import DEFAULT_GAME_CONFIGURATION
from scriptcraft.core.GameMap import GameMap
from tests.core.Game import BaseGameTestCase
from scriptcraft.utils import *


class GameViewer(Canvas):

    def __init__(self, master):
        Canvas.__init__(self, master, width=800, height=600, bg='yellow')
        self.pack(expand=YES, fill=BOTH)

        # bindings
        #self.canvas.bind('<B1-Motion>', self.move_event)
        #self.canvas.bind('<ButtonRelease-1>', self.release)
        #self.canvas.bind('<MouseWheel>', self.roll_wheel)
        #self.canvas.bind('<Button-4>', self.roll_wheel)
        #self.canvas.bind('<Button-5>', self.roll_wheel)

        # own attributes
        self.zoom = 1.0
        self.delta = (0.0, 0.0)
        self._scaled_images_cache = {}

        # for testing
        self.create_rectangle(50, 25, 150, 75, fill="blue")
        self.create_image(0, 0,
                          image=self._get_scaled_sprite('flat_field', 0.4),
                          anchor=NW)



    @memoized
    def _get_image(self, name):
        """ Return (PIL.)Image instance. """
        path = '../graphic/%s.png' % name
        image = Image.open(path)
        return image

    def _get_scaled_sprite(self, name, factor):
        # if cached, return cached value
        id = (name, factor)
        image = self._scaled_images_cache.get(id, None)
        if image:
            return image

        # otherwise compute, cache and return
        image = self._get_image(name)
        width, height = 256, 288
        new_width, new_height = width*factor+2, height*factor+2
        image = image.resize((new_width, new_height), Image.NEAREST)
        image = ImageTk.PhotoImage(image)

        # no problem with bug connected with reference count --
        # caching keeps image reference
        self._scaled_images_cache[id] = image
        return image

    def _clear_scaled_images_cache(self):
        """ Due to reference count bug in Image all images will be
        removed from memory! Make sure that you don't need any image
        in cache. """
        self._scaled_images_cache = {}


class ClientApplication(Frame):

    def __init__(self, master):
        Frame.__init__(self, master)
        self._init_gui()

    def _init_gui(self):
        self.pack(expand=YES, fill=BOTH)
        self._game_viewer = GameViewer(self)


if __name__ == "__main__":
    root = Tk()
    app = ClientApplication(master=root)
    app.mainloop()
    root.destroy()
