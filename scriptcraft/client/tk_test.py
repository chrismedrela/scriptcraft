#!/usr/bin/env python
#-*- coding:utf-8 -*-

from Tkinter import *
from PIL import Image, ImageTk
import time



class Application(Frame):
    def createWidgets(self):
        self.canvas = Canvas(self, width=800, height=600, bg='yellow')
        self.canvas.pack(expand=YES, fill=BOTH)
        #self.canvas.create_rectangle(50, 25, 150, 75, fill="blue")

        self.zoom = 1.0
        self.delta = (0.0, 0.0)
        self.first_draw()
        self.canvas.bind('<B1-Motion>', self.move_event)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<MouseWheel>', self.roll_wheel)
        self.canvas.bind('<Button-4>', self.roll_wheel)
        self.canvas.bind('<Button-5>', self.roll_wheel)

    def first_draw(self):
        self.canvas.delete('myPhoto')

        t2 = time.time()
        img = Image.open('/media/BC4C-2EB9/Programowanie/Python'
                         '/scriptcraft/scriptcraft/graphic/flat_field.png')
        t = time.time()
        img = img.resize((256*self.zoom+2, 288*self.zoom+2), Image.NEAREST)
        print 'scaling image', time.time()-t, 'sek'
        image = ImageTk.PhotoImage(img)
        self.image = [image]
        self.N = N = 96
        self.i = 0
        for i in xrange(0, N):
            for j in xrange(0, N):
                x, y = self.to_screen_coordinate((i, j))
                self.canvas.create_image(x, y, image=image, anchor=NW, tags=['myPhoto', 'r'+str(i)])
        print 'redraw after scaling in', time.time()-t2, 'sec'

    def redraw_after_scaling(self, dzoom, (x, y), j):
        img = Image.open('/media/BC4C-2EB9/Programowanie/Python'
                         '/scriptcraft/scriptcraft/graphic/flat_field.png')
        img = img.resize((256*self.zoom+2, 288*self.zoom+2), Image.NEAREST)
        image = ImageTk.PhotoImage(img)
        self.image.append(image)

        zoom = self.zoom
        self.canvas.scale('myPhoto', x, y, dzoom, dzoom)
        for i in xrange(self.N):
            if self.zoom == zoom:
                self.canvas.itemconfigure('r'+str(i), image=image)
            self.update()

    def roll_wheel(self, event):
        delta = 0
        # respond to Linux or Windows wheel event
        if event.num == 5 or event.delta == -120:
            delta -= 1
        if event.num == 4 or event.delta == 120:
            delta += 1

        WSP = 1.05
        self.zoom *= WSP**delta

        #self.canvas.scale('myPhoto', 0, 0, S, S)
        self.i += 1
        self.redraw_after_scaling(WSP**delta, (event.x, event.y), self.i-1)

    def release(self, event):
        if hasattr(self, '_last_pos'):
            del self._last_pos

    def move_event(self, event):
        if not hasattr(self, '_last_pos'):
            self._last_pos = (event.x, event.y)
            return

        dy = event.y - self._last_pos[1]
        dx = event.x - self._last_pos[0]
        self._last_pos = (event.x, event.y)

        self.canvas.move('myPhoto', dx, dy)
        import time
        t = time.time()
        self.update()

    def to_screen_coordinate(self, (x, y)):
        return (128*self.zoom*(x-y-2*self.delta[0]),
                72*self.zoom*(x+y-2*self.delta[1]))

    def to_game_coordinate(self, (x, y)):
        return (x/256.0/self.zoom + y/144.0/self.zoom + self.delta[0] + self.delta[1],
                -x/256.0/self.zoom + y/144.0/self.zoom - self.delta[0] + self.delta[1])


    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack(expand=YES, fill=BOTH)
        self.createWidgets()


root = Tk()
app = Application(master=root)
app.mainloop()
root.destroy()
