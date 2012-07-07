#!/usr/bin/env python
#-*- coding:utf-8 -*-

import ConfigParser
try:
    import cPickle as pickle
except:
    import pickle
import itertools
import math
import os.path
from Queue import Queue
import random
import time
import threading
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
                                   load_game_map, InvalidGameMapData, cmds)
from scriptcraft.gamesession import (GameSession, SystemConfiguration,
                                     AlreadyExecuteGame)
from scriptcraft.utils import *



class GameViewer(Canvas):
    """GameViewer is canvas widget to display a scriptcraft Game
    instance. It provides scrolling and zooming the map and selecting
    fields.

    About selecting:

    When a mouse motion is detected and the selection changed then
    <<selection-changed>> event is emitted. You can find out which
    field is selected by checking GameViewer.selection_position which
    is (x, y) tuple or None.

    """

    SCROLLING_SENSITIVITY = 2**(1/2.0) # in (1, +inf); greater means faster scrolling
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
    MAX_ZOOM = 1.0
    MIN_ZOOM = 1.0/4

    CORNER_TEXT_POSITION = (15, 20) # position at screen
    CORNER_TEXT_FONT_OPTIONS = {'size':12,
                              'weight':'bold'}
    CORNER_TEXT_COLOR = 'red'
    CORNER_TEXT_INITIAL_TEXT = ''

    LOADING_INDICATOR_POSITION = (-45, 15)
    LOADING_INDICATOR_SPEED = int(-360*1.5) # degrees per second
    FREQUENCY_OF_UPDATING_ANIMATIONS = 50 # ms

    FREQUENCY_OF_CHECKING_QUERY = 100 # ms
    COLOR_OF_GROUND_IMITATION = '#336633'

    GRID_COLOR = '#555555'

    def __init__(self, master):
        Canvas.__init__(self, master, width=800, height=600, bg='black')
        self.pack(expand=YES, fill=BOTH)

        # To enable receiving wheel rolling events under windows, we
        # need this action before bindings:
        self.focus_set()

        # bindings
        self.bind('<B1-Motion>',
                  self._mouse_motion_with_button_pressed_callback)
        self.bind('<Motion>', self._mouse_motion_callback)
        self.bind('<ButtonRelease-1>', self._release_callback)
        self.bind('<MouseWheel>', self._roll_wheel_callback)
        self.bind('<Button-4>', self._roll_wheel_callback)
        self.bind('<Button-5>', self._roll_wheel_callback)
        self.bind('<Button-1>', self._click_callback)
        self.bind("<Configure>", self._resized_callback)

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
        self._trees_ids_by_position = {}
        self._queue = Queue()
        self._compute_ground_image_flag = False
        self._corner_text_id = self.create_text(
            GameViewer.CORNER_TEXT_POSITION[0],
            GameViewer.CORNER_TEXT_POSITION[1],
            anchor=NW, text=GameViewer.CORNER_TEXT_INITIAL_TEXT,
            font=tkFont.Font(**GameViewer.CORNER_TEXT_FONT_OPTIONS),
            fill=GameViewer.CORNER_TEXT_COLOR,
            tag=['interface'])
        image = self._get_image('loading')
        self._loading_image = ImageTk.PhotoImage(image)
        self._loading_indicator_id = self.create_image(
            self._loading_indicator_position[0],
            self._loading_indicator_position[1],
            image=self._loading_image,
            state=HIDDEN, anchor=NW,
            tags=['interface'])
        self._loading_indicator_turned_on = False
        self._update_loading_indicator()
        self._check_queue()

    @property
    def _loading_indicator_position(self):
        x, y = GameViewer.LOADING_INDICATOR_POSITION
        width, height = self.winfo_width(), self.winfo_height()
        result = (x if x >= 0 else width+x,
                  y if y >= 0 else height+y)
        return result

    def _update_loading_indicator(self):
        if self._loading_indicator_turned_on:
            image = self._get_image('loading')
            angle = time.time()*GameViewer.LOADING_INDICATOR_SPEED % 360
            image = image.rotate(angle, resample=Image.BICUBIC)
            self._loading_image = ImageTk.PhotoImage(image)
            self.itemconfig(self._loading_indicator_id,
                            image=self._loading_image)
        self.master.after(GameViewer.FREQUENCY_OF_UPDATING_ANIMATIONS,
                          self._update_loading_indicator)

    @log_on_enter('set game in game viewer', mode='only time')
    def set_game(self, game):
        """ Attribute game should be scriptcraft game instance or
        None.

        In this method game instance passed during previous
        call is used. The previous game instance cannot be modified
        since the previous call!

        Use set_game(None) and set_game(new_game) to force redrawing
        ground and delete current selection.
        """

        #import ipdb; ipdb.set_trace()
        previous_game = self._game
        self._game = game

        if previous_game:
            self.delete('non-cached')

        if not game:
            # reset queue
            self._queue = Queue()
            self._compute_ground_image_flag = False

            # selection position
            self._set_selection_position(None, force_emitting=True)

            # force redrawing ground during next set_game call
            self._ground_image_cache = None
            if 'ground' in self._scaled_images_cache:
                del self._scaled_images_cache['ground']

            # reset zoom and delta
            self._zoom = 1.0
            self._delta = (-5.0, 0.0)

            # hide loading indicator
            self.show_loading_indicator(False)

            # other stuff
            self._trees_ids_by_position.clear()
            self.delete('tree')
        else:
            # selection position
            self._set_selection_position(self.selection_position,
                                         force_emitting=True)

            # draw game
            self._draw_game(game, old_game=previous_game)

    def set_corner_text(self, text):
        self.itemconfigure(self._corner_text_id,
                           text=text)

    def show_loading_indicator(self, state):
        assert isinstance(state, bool)
        self._loading_indicator_turned_on = state
        state = NORMAL if state else HIDDEN
        self.itemconfig(self._loading_indicator_id,
                        state=state)

    def _draw_game(self, game, old_game):
        # draw imitation of ground
        size = self._game.game_map.size
        points = [(0, 0), (0, size[1]), (size[0], size[1]), (size[0], 0)]
        points = [self._to_screen_coordinate(pos) for pos in points]
        points = [coord for pos in points for coord in pos]
        self.create_polygon(points,
                            fill=GameViewer.COLOR_OF_GROUND_IMITATION,
                            tags=['game', 'non-cached', 'layer-1'])

        # draw ground
        self._draw_ground()

        # remove deleted trees
        tree_positions = [position for (position, obj)
                          in self._game.game_map._objs.items()
                          if isinstance(obj, Tree)]
        tree_positions = set(tree_positions)

        if old_game is not None:
            old_tree_positions = [
                position for (position, obj)
                in old_game.game_map._objs.items()
                if isinstance(obj, Tree)]
            old_tree_positions = set(old_tree_positions)
        else:
            old_tree_positions = set()

        deleted_trees = old_tree_positions - tree_positions
        for position in deleted_trees:
            self.delete(self._trees_ids_by_position[position])
            del self._trees_ids_by_position[position]

        # draw objects
        def draw_arrow(source, destination, type='red'):
            assert type in ('red', 'blue')
            delta = map(lambda (a, b): a-b, zip(destination,
                                                source))
            d = direction.FROM_RAY[tuple(delta)]
            direction_name = direction.TO_FULL_NAME[d]
            self._draw('arrow-%s-%s' % (type, direction_name),
                       source, layer=2)

        objs = sorted(self._game.game_map._objs.items(),
                      key=lambda (pos, obj): pos[0]+pos[1])
        for position, obj in objs:
            if isinstance(obj, Tree): # draw tree
                if position not in old_tree_positions:
                    name = 'tree%s' % obj.type
                    id_ = self._draw(name, position, layer=3, cached=True,
                                     extra_tags=['tree'])
                    self._trees_ids_by_position[position] = id_
                else:
                    pass
                    self.tag_raise(self._trees_ids_by_position[position])

            elif isinstance(obj, MineralDeposit): # draw minerals
                if obj.minerals:
                    self._draw('minerals', position, layer=3)
                else:
                    self._draw('minerals-ex', position, layer=3)

            elif isinstance(obj, Unit): # draw unit
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
                self._draw(sprite_name, position, layer=3)

                # draw label for the unit
                x, y = self._to_screen_coordinate(position)
                color = '#' + "%02x%02x%02x" % unit.player.color
                font = self._get_font_for_current_zoom()
                # this operation costs a lot [optimization]
                self.create_text(x, y, fill=color, text=unit.player.name,
                                 font=font, tags=['layer-3', 'game', 'text',
                                                  'non-cached'],
                                 state=NORMAL if font else HIDDEN)

                # draw arrows indicating executing action (or fire explosion)
                if isinstance(unit.action, actions.MoveAction):
                    draw_arrow(unit.action.source,
                               unit.action.destination,
                               type='blue')
                if isinstance(unit.action, actions.GatherAction):
                    draw_arrow(unit.position,
                               unit.action.source)
                elif isinstance(unit.action, actions.StoreAction):
                    destination_unit = self._game.units_by_IDs[
                        unit.action.storage_ID]
                    destination = destination_unit.position
                    draw_arrow(unit.position, destination)
                elif isinstance(unit.action, actions.FireAction):
                    self._draw('explosion', unit.action.destination, layer=3)

        # draw lines (debug)
        def draw_grid():
            line_color = GameViewer.GRID_COLOR

            for x in xrange(0, game.game_map.size[1] + 1):
                start_position = (0, x)
                end_position = (game.game_map.size[0], x)
                start_position = self._to_screen_coordinate(start_position)
                end_position = self._to_screen_coordinate(end_position)
                self.create_line(*(start_position + end_position),
                                 fill=line_color,
                                 tag=['layer-1.5', 'game', 'non-cached'])

            for y in xrange(0, game.game_map.size[0] + 1):
                start_position = (y, 0)
                end_position = (y, game.game_map.size[1])
                start_position = self._to_screen_coordinate(start_position)
                end_position = self._to_screen_coordinate(end_position)
                self.create_line(*(start_position + end_position),
                                 fill=line_color,
                                 tag=['layer-1.5', 'game', 'non-cached'])

        draw_grid()

        # raise layers
        self.tag_raise('layer-1')
        self.tag_raise('layer-1.5')
        self.tag_raise('layer-2')
        self.tag_raise('layer-3')
        self.tag_raise('interface')

    def _draw_ground(self):
        if self._ground_image_cache:
            self._draw('ground', (0, 0), layer=1)
            self.tag_lower('layer-1')
        elif not self._compute_ground_image_flag:
            target = lambda: self._compute_ground_image_asynch(self._queue)
            thread = threading.Thread(target=target)
            thread.start()

    def _compute_ground_image_asynch(self, queue):
        self._get_ground_image()
        queue.put('ready')
        self._compute_ground_image_flag = False

    def _check_queue(self):
        if not self._queue.empty():
            command = self._queue.get_nowait()
            assert command == 'ready'
            self._draw_ground()
        self.master.after(GameViewer.FREQUENCY_OF_CHECKING_QUERY,
                          self._check_queue)

    @memoized
    def _gradient(self, align):
        assert align in ('ns', 'we')
        gradient = Image.new('L', (255, 1))
        for x in range(255):
            gradient.putpixel((254-x, 0), x)
        gradient = gradient.resize((255, 255))
        if align == 'ns':
            gradient = gradient.rotate(45-180, expand=True)
        elif align == 'we':
            gradient = gradient.rotate(-45, expand=True)
        gradient = gradient.resize((GameViewer.TILE_WIDTH+2,
                                    GameViewer.TILE_HEIGHT+2))
        return gradient

    def _draw(self, name, position, layer, state=NORMAL,
              extra_tags=None, cached=False):
        """ Draw sprite with name 'name' at position 'position' in
        game coordinates."""

        extra_tags = extra_tags or []
        tags = [name, 'layer-%s' % layer, 'game']
        if not cached:
            tags.append('non-cached')
        position = self._to_screen_coordinate(position)
        x, y = self._to_image_position(name, position)
        image = self._get_scaled_sprite(name)
        id_ = self.create_image(x, y, image=image, anchor=NW,
                                state=state, tags=tags+extra_tags)
        return id_

    def _get_font_for_current_zoom(self):
        size = int(12.2*self._zoom)
        if size < 9:
            if size >= 6:
                return tkFont.Font(size=9)
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

    def _get_ground_tile(self, name, (x, y)):
        x %= GameViewer.GROUND_TILES_IN_ROW
        y %= GameViewer.GROUND_TILES_IN_COLUMN

        key = (name, (x, y))
        if key not in self._ground_tiles_cache:
            start_point_x = x*GameViewer.GROUND_TILE_WIDTH
            start_point_y = y*GameViewer.GROUND_TILE_HEIGHT
            image = self._get_image(name) # '.'+name for testing
            image = image.convert('RGBA')
            box = (start_point_x, start_point_y,
                GameViewer.GROUND_TILE_WIDTH+start_point_x,
                GameViewer.GROUND_TILE_HEIGHT+start_point_y)
            croped = image.crop(box)
            rotated = croped.rotate(-45, expand=True,
                                    resample=Image.BICUBIC)
            scaled = rotated.resize((GameViewer.TILE_WIDTH+2,
                                     GameViewer.TILE_HEIGHT+2))
            self._ground_tiles_cache[key] = scaled
        return self._ground_tiles_cache[key]

    @log_on_enter('GameViewer._get_ground_image', mode='only time')
    def _get_ground_image(self):
        """ Return (PIL.)Image instance. """

        if self._ground_image_cache is None: # then compute it and cache
            log('computing ground image')

            def blend(image_nw, image_ne, image_se, image_sw,
                      gradient_ns, gradient_we):
                if image_nw == image_ne == image_se == image_sw:
                    return image_nw
                image_w = (Image.composite(image_nw, image_sw, gradient_ns)
                           if image_nw != image_sw
                           else image_nw)
                image_e = (Image.composite(image_ne, image_se, gradient_ns)
                           if image_ne != image_se
                           else image_ne)
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
                tile_ne = self._get_ground_tile(tile_name_ne, (x, y))
                tile_se = self._get_ground_tile(tile_name_se, (x, y))
                tile_sw = self._get_ground_tile(tile_name_sw, (x, y))

                tile = blend(tile_nw, tile_ne, tile_se, tile_sw,
                             gradient_ns, gradient_we)
                box = [GameViewer.TILE_WIDTH/2.0*(x-y+size[1]),
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
        delta = 0 if name == 'ground' else 2
        new_width, new_height = (int(width*self._zoom)+delta,
                                 int(height*self._zoom)+delta)
        if width != new_width: # resize if it's necessary
            image = image.resize((new_width, new_height), Image.NEAREST)
        image = ImageTk.PhotoImage(image)

        # no problem with bug connected with reference count --
        # caching keeps image reference
        self._scaled_images_cache[name] = image
        return image

    def _to_screen_coordinate(self, (x, y), delta=None, zoom=None):
        """ From game coordinates. """
        zoom = zoom or self._zoom
        delta = delta or self._delta
        return (32*zoom*(x-y-2*delta[0]),
                16*zoom*(x+y-2*delta[1]))

    def _to_game_coordinate(self, (x, y), delta=None, zoom=None):
        """ From screen coordinates. """
        zoom = zoom or self._zoom
        delta = delta or self._delta
        return (x/64.0/zoom + y/32.0/zoom \
                + delta[0] + delta[1],
                -x/64.0/zoom + y/32.0/zoom \
                - delta[0] + delta[1])

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

    def _set_zoom(self, zoom, (XS, YS)):
        """ Set zoom. The point (XS, YS) in screen coordinate doesn't
        move."""

        # bound zoom
        zoom = max(zoom, GameViewer.MIN_ZOOM)
        zoom = min(zoom, GameViewer.MAX_ZOOM)
        if zoom == self._zoom:
            # zoom hasn't been changed
            return

        # It clears cache of scaled images. Due to reference count bug
        # all images will be removed from memory!

        # compute new self._delta and self._zoom
        xS, yS = self._to_game_coordinate((XS, YS))
        delta = [-XS/64.0/zoom + xS/2.0 - yS/2.0,
                 -YS/32.0/zoom + xS/2.0 + yS/2.0]
        self._zoom, old_zoom = zoom, self._zoom
        cleared_delta = self._clear_delta(delta)
        self._delta = cleared_delta
        delta_delta = (cleared_delta[0]-delta[0],
                       cleared_delta[1]-delta[1])

        # scale all images
        with log_on_enter('GameViewer._set_zoom: rescaling images',
                          mode='only time'):
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
        self.scale('game', XS, YS, factor, factor)
        self.move('game',
                  -delta_delta[0]*64.0*self._zoom,
                  -delta_delta[1]*32.0*self._zoom)

    def _clear_delta(self, delta):
        if not self._game:
            return delta

        size = self.winfo_width(), self.winfo_height()
        center_of_screen = (size[0]/2, size[1]/2)
        map_width = self._game.game_map.size[0]
        map_height = self._game.game_map.size[1]
        pos = self._to_game_coordinate(center_of_screen, delta=delta)
        if (0 <= pos[0] < map_width and
            0 <= pos[1] < map_height):
            return delta

        # If we are here it means that the delta is invalid.
        # 1. Find valid position
        pos = (min(map_width, max(0, pos[0])),
               min(map_height, max(0, pos[1])))
        # 2. Find delta which fullfils the condition:
        # _to_screen_coordinate(pos) == center_of_screen
        delta = (-(center_of_screen[0]/32.0/self._zoom - pos[0] + pos[1])/2.0,
                 -(center_of_screen[1]/16.0/self._zoom - pos[0] - pos[1])/2.0)
        return delta

    def _set_selection_position(self, value, force_emitting=False):
        old_selection = self.selection_position
        self.selection_position = value
        if old_selection != value or force_emitting:
            self.event_generate('<<selection-changed>>')

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

    def _mouse_motion_with_button_pressed_callback(self, event):
        # scrolling map

        if self._game and self._last_mouse_position:
            with log_on_enter('moving everything', mode='only time'):
                dx, dy = (event.x - self._last_mouse_position[0],
                          event.y - self._last_mouse_position[1])
                delta = (self._delta[0] - dx/64.0/self._zoom,
                         self._delta[1] - dy/32.0/self._zoom)
                delta = self._clear_delta(delta)
                dx, dy = ((self._delta[0]-delta[0])*64.0*self._zoom,
                          (self._delta[1]-delta[1])*32.0*self._zoom)
                self._delta = delta
                self.move('game', dx, dy)

        self._last_mouse_position = (event.x, event.y)

    def _mouse_motion_callback(self, event):
        if not self._game:
            return

        # info about field/unit under mouse -- update corner text
        pos = self._to_game_coordinate((event.x, event.y))
        pos = tuple(map(lambda x: int(math.floor(x)), pos))
        if self._game.game_map[pos].valid_position:
            self._set_selection_position(pos)
        else:
            self._set_selection_position(None)

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
                pass

    def _resized_callback(self, event):
        # update delta
        delta = self._clear_delta(self._delta)
        dx, dy = ((self._delta[0]-delta[0])*64.0*self._zoom,
                  (self._delta[1]-delta[1])*32.0*self._zoom)
        self._delta = delta
        self.move('game', dx, dy)

        # update loading indicator's position
        self.coords(
            self._loading_indicator_id,
            self._loading_indicator_position[0],
            self._loading_indicator_position[1])


class ClientApplication(Frame):

    CONFIGURATION_FILE = 'configuration.ini'
    FREQUENCY_OF_CHECKING_QUERY = 50 # ms
    MAPS_DIRECTORY = 'maps'
    GAMES_DIRECTORY = 'games'

    MENU_GAME_LABEL = "Gra"
    NEW_GAME_LABEL = "Stwórz nową grę..."
    SAVE_GAME_LABEL = "Zapisz grę"
    LOAD_GAME_LABEL = "Wczytaj grę..."
    ADD_PLAYER_LABEL = "Dodaj nowego gracza..."
    SET_PROGRAM_LABEL = "Ustaw program zaznaczonej jednostce..."
    SET_STAR_PROGRAM_LABEL = "Ustaw star program zaznaczonej jednostce"
    DELETE_PROGRAM_LABEL = "Usuń program zaznaczonej jednostce"
    TIC_LABEL = "Symuluj jedną turę gry"
    TIC_IN_LOOP_LABEL = "Symulacja gry w pętli"
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

    TITLE_INVALID_CONFIGURATION_FILE = 'Niepoprawny plik konfiguracji'
    INVALID_CONFIGURATION_FILE = ('Nie można wczytać ustawień z pliku '
                                  'konfiguracji. Aplikacja zostanie '
                                  'zamknięta. Sprawdź zawartość pliku "' + \
                                  CONFIGURATION_FILE + \
                                  '".')

    DIRECTION_TO_NAME = {
        direction.N : 'północ',
        direction.W : 'zachód',
        direction.S : 'południe',
        direction.E : 'wschód',
    }

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
        self._tic_in_loop = BooleanVar(False)
        self._init_gui()
        self._game = None
        self._game_session = None
        self._queue = Queue()
        self._master = master
        self._check_queue()
        self._load_configuration_file()
        if len(sys.argv) == 2 and sys.argv[1].lower() == '--test':
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
            system_configuration=self.system_configuration,
            game=game)
        self.set_game_session(session)
        game = session.game

        # modify game (set programs)
        def set_program(unit_id, filename):
            program = Program(Language.PYTHON,
                              open('scriptcraft/.tmp/'+filename).read())
            game.set_program(game.units_by_IDs[unit_id], program)
        try:
            set_program(8, 'build_tank.py')
            for i in xrange(3,7):
                set_program(i, 'move_randomly.py')
            for i in xrange(9,13):
                set_program(i, 'move_randomly.py')
        except Exception:
            log_exception('cannot set program for testing game')

        self._set_game(game)

    def _check_queue(self):
        if not self._queue.empty():
            command = self._queue.get_nowait()
            assert command == 'ready'
            self._game_viewer.show_loading_indicator(False)
            self._set_game(self._game_session.game)
            if self._tic_in_loop.get():
                self._tic()
        self.master.after(ClientApplication.FREQUENCY_OF_CHECKING_QUERY,
                          self._check_queue)

    def _load_configuration_file(self):
        try:
            filename = datafile_path(ClientApplication.CONFIGURATION_FILE)
            self.system_configuration = SystemConfiguration(filename)
        except (IOError, ValueError, ConfigParser.Error) as ex:
            log_exception('invalid configuration file')
            self._warning(
                ClientApplication.TITLE_INVALID_CONFIGURATION_FILE,
                ClientApplication.INVALID_CONFIGURATION_FILE
            )
            global root
            root.destroy()


    def _init_gui(self):
        self.pack(expand=YES, fill=BOTH)
        global root
        root.protocol("WM_DELETE_WINDOW", self._quit_callback)
        self._game_viewer = GameViewer(self)
        self._game_viewer.bind('<<selection-changed>>',
                               self._selection_changed_callback)
        self._create_menubar()
        self._create_keyboard_shortcuts()

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
        self._game_menu.add_checkbutton(
            label=ClientApplication.TIC_IN_LOOP_LABEL,
            command=lambda: self._tic_in_loop_callback(switch=False),
            state=DISABLED,
            variable=self._tic_in_loop)
        self._game_menu.add_separator()
        self._game_menu.add_command(
            label=ClientApplication.QUIT_LABEL,
            command=self._quit_callback)

        menubar.add_command(label=ClientApplication.MENU_ABOUT_LABEL,
                            command=self._about_callback)

        global root
        root.config(menu=menubar)

    def _create_keyboard_shortcuts(self):
        # new game
        self._game_menu.entryconfigure(
            ClientApplication.NEW_GAME_LABEL,
            accelerator="Ctrl+N")
        args = ("<Control-n>", lambda w: self._new_game_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

        # save game
        self._game_menu.entryconfigure(
            ClientApplication.SAVE_GAME_LABEL,
            accelerator="Ctrl+S")
        args = ("<Control-s>", lambda w: self._save_game_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

        # load game
        self._game_menu.entryconfigure(
            ClientApplication.LOAD_GAME_LABEL,
            accelerator="Ctrl+O")
        args = ("<Control-o>", lambda w: self._load_game_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

        # add player
        self._game_menu.entryconfigure(
            ClientApplication.ADD_PLAYER_LABEL,
            accelerator="Ctrl+A")
        args = ("<Control-a>", lambda w: self._add_player_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

        # tic item
        self._game_menu.entryconfigure(
            ClientApplication.TIC_LABEL,
            accelerator="T")
        args = ("<t>", lambda w: self._tic_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

        # tic in loop item
        self._game_menu.entryconfigure(
            ClientApplication.TIC_IN_LOOP_LABEL,
            accelerator='spacja')
        self._game_viewer.bind("<space>", \
            lambda w: self._tic_in_loop_callback(switch=True))

        # quit program
        self._game_menu.entryconfigure(
            ClientApplication.QUIT_LABEL,
            accelerator="Ctrl+Q")
        args = ("<Control-q>", lambda w: self._quit_callback())
        self._game_viewer.bind(*args)
        self._game_menu.bind(*args)

    # callbacks ----------------------------------------------------------

    @log_on_enter('use case: new game', lvl='info')
    def _new_game_callback(self):
        if not self._ask_if_delete_current_game_if_exists():
            return

        map_filename = tkFileDialog.askopenfilename(
            title=ClientApplication.CHOOSE_MAP_FILE,
            filetypes=ClientApplication.MAP_FILE_TYPES,
            initialdir=datafile_path(ClientApplication.MAPS_DIRECTORY),
            parent=self,
        )
        if not map_filename:
            return

        directory = tkFileDialog.askdirectory(
            title=ClientApplication.CHOOSE_DIRECTORY_FOR_NEW_GAME,
            initialdir=datafile_path(ClientApplication.GAMES_DIRECTORY),
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
                game_session = GameSession(directory,
                                           self.system_configuration,
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
            initialdir=datafile_path(ClientApplication.GAMES_DIRECTORY),
            mustexist=True,
            parent=self,
        )
        if not directory:
            return

        try:
            game_session = GameSession(directory, self.system_configuration)
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
        pos = self._game_viewer.selection_position
        if self._game is None:
            return

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
        self._tic()

    @log_on_enter('use case: switch tic in loop', lvl='info')
    def _tic_in_loop_callback(self, switch):
        if switch:
            self._tic_in_loop.set(not self._tic_in_loop.get())
        if self._tic_in_loop.get():
            self._tic()

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

    def _selection_changed_callback(self, event):
        pos = self._game_viewer.selection_position
        #if pos is not None:
        #    self._print_info_about_field_at(pos)
        if pos is None:
            text = " "
        else:
            field = self._game.game_map[pos]
            obj = field.maybe_object
            if obj is None:
                obj_info = ""
            elif isinstance(obj, Tree):
                obj_info = "Drzewa."
            elif isinstance(obj, MineralDeposit):
                obj_info = "Złoża minerałów (%d jednostek minerałów)." % obj.minerals
            elif isinstance(obj, Unit):
                # type of the unit
                if obj.type.main_name == '4': # base
                    obj_info = "Baza"
                elif obj.type.main_name == '5': # miner
                    state = ('pełny' if obj.minerals else 'pusty')
                    obj_info = "Zbieracz minerałów (%s)" % state
                elif obj.type.main_name == '6': # tank
                    obj_info = "Czołg"
                else:
                    assert False, 'oops, unknown unit type %r' % unit.type

                # player
                obj_info += ' gracza %s.' % obj.player.name

                # command
                if isinstance(obj.command, cmds.StopCommand):
                    command_info = 'stop'
                elif isinstance(obj.command, cmds.MoveCommand):
                    d = ClientApplication.DIRECTION_TO_NAME[obj.command.direction]
                    command_info = 'idź na %s' % d
                elif isinstance(obj.command, cmds.ComplexMoveCommand):
                    command_info = 'idź do (%d, %d)' \
                      % obj.command.destination
                elif isinstance(obj.command, cmds.ComplexGatherCommand):
                    command_info = 'zbieraj minerały z (%d, %d)' \
                      % obj.command.destination
                elif isinstance(obj.command, cmds.FireCommand):
                    command_info = 'ogień na (%d, %d)' \
                      % obj.command.destination
                elif isinstance(obj.command, cmds.ComplexAttackCommand):
                    command_info = 'atak na (%d, %d)' \
                      % obj.command.destination
                elif isinstance(obj.command, cmds.BuildCommand):
                    command_info = 'buduj "%s"' \
                      % obj.command.unit_type_name
                obj_info += ' Komenda: %s.' % command_info
            else:
                assert False, 'oops, unknown object on map %r' % obj
            field_info = "Pole (%d, %d)." % (pos[0], pos[1])
            text = " ".join([field_info, obj_info])

        self._game_viewer.set_corner_text(text)
        self._refresh_game_menu_items_state()



    # other methods -------------------------------------------------------
    def _tic(self):
        try:
            self._game_viewer.show_loading_indicator(True)
            self._game_session.tic(self._queue)
        except AlreadyExecuteGame as ex:
            log('already execute game')

    @log_on_enter('set game session')
    def set_game_session(self, game_session):
        self._game_session = game_session
        self._set_game(None)
        self._tic_in_loop.set(False)
        self._queue = Queue()
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
                   ClientApplication.TIC_LABEL,
                   ClientApplication.TIC_IN_LOOP_LABEL]
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


def run_with_profiling():
    # profile run function
    filename = '.stats'
    import cProfile
    cProfile.run('run()', filename)
    import pstats
    p = pstats.Stats(filename)
    p.strip_dirs()
    p.sort_stats('cumulative')
    p.dump_stats(filename)
    p.print_stats(25)

def run():
    # prevent "errors occured" message box in py2exe distribution
    turn_off_standard_streams_if_it_is_py2exe_distribution()

    # run it!
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
    run_with_profiling()
