import gc
import threading as thr
from math import ceil

import numpy as np
import pyglet as pyg
from pyglet.window import FPSDisplay, key

from misc.ProjSettings import RenderingSettings as rs
from ui.game_objects import Room

_escaped = False
events = {}
known_rooms = {'new': {}, 'known': {}}
room_objects = {}
entities = []

keys = key.KeyStateHandler()

from threading import RLock

lock = RLock()


def toFixed(numObj, digits=0):
    return float(f"{numObj:.{digits}f}")


class Camera:
    def __init__(self):
        self.size = rs.window_size
        self.position, self.velocity = np.array([3000., 3000., 1.],), np.array([.0, .0, .0])
        self.d_position = np.array([.0, .0, .0])
        self.friction = np.array([-.12, -.12, -.2])
        self.acceleration = np.array([.0, .0, .0])
        self.max_velocity = np.array([4., 4., 1.])
        self.max_position = np.array([18000., 18000., 5.])
        self.min_position = np.array([0., 0., 0.5])

    def movement(self, dt):
        self.acceleration += self.velocity * self.friction
        self.velocity += (self.acceleration * dt)

    def limit_velocity(self):

        if sum(map(np.square, self.velocity)) > np.square(self.max_velocity[0]):
            self.velocity = (self.velocity / np.linalg.norm(self.velocity)) * self.max_velocity[0]
        if abs(self.velocity[0]) < .005: self.velocity[0] = 0
        if abs(self.velocity[1]) < .005: self.velocity[1] = 0
        if abs(self.velocity[2]) < .002: self.velocity[2] = 0

    def update(self, dt):
        self.movement(dt)
        self.acceleration *= 0
        self.limit_velocity()

        if sum(map(np.square, self.velocity)) > 0:
            self.position += self.velocity * dt + (self.acceleration * .5) * dt ** 2
            if sum(map(np.square, self.position)) > np.square(self.max_position[0]):
                self.position = (self.position / np.linalg.norm(self.position)) * self.max_position[0]
            if sum(map(np.square, self.position)) < np.square(self.min_position[0]):
                self.position = (self.position / np.linalg.norm(self.position)) * self.min_position[0]

    def get_width(self):
        return self.size[0]

    def get_height(self):
        return self.size[1]

    @property
    def fov_rectangle(self):
        return (self.position[0] - (self.get_width() * self.position[2] / 2),
                self.position[1] - (self.get_height() * self.position[2] / 2),
                (self.get_width() * self.position[2]),
                (self.get_height() * self.position[2]))

    @property
    def centred_rectangle(self):
        return (3000 - (self.get_width() * self.position[2] / 2),
                3000 - (self.get_height() * self.position[2] / 2),
                (self.get_width() * self.position[2]),
                (self.get_height() * self.position[2]))

    @property
    def fod_rectangle(self):
        return (self.position[0] - ((self.get_width() + 100 / self.position[2]) * self.position[2] / 2),
                self.position[1] - ((self.get_height() + 100 / self.position[2]) * self.position[2] / 2),
                ((self.get_width() + 100 / self.position[2]) * self.position[2]),
                ((self.get_height() + 100 / self.position[2]) * self.position[2]))

    @property
    def tiled_area(self):
        fod = self.fod_rectangle
        return (int(fod[0] // rs.room_size[0]), int(fod[1] // rs.room_size[1]),
                ceil((fod[0] + fod[2]) / rs.room_size[0]), ceil((fod[1] + fod[3]) / rs.room_size[1]))

    def repr_tiled_area(self):
        tr = self.tiled_area
        return (tr[0] * rs.room_size[0],
                tr[1] * rs.room_size[1],
                tr[2] * rs.room_size[0] - tr[0] * rs.room_size[0],
                tr[3] * rs.room_size[1] - tr[1] * rs.room_size[1])

    def local_move_x(self, x):
        self.acceleration[0] = x / self.position[2]

    def local_move_y(self, y):
        self.acceleration[1] = y / self.position[2]

    def local_zoom(self, z):
        self.acceleration[2] = z / self.position[2]

    def get_cords(self):
        pass


camera = Camera()


class DrawThread:
    def __init__(self, window):
        self.frame_counter = 0
        self.window: pyg.window.Window = window
        self.halted = thr.Event()
        self.room_per_frame = 0
        self.frametime_buffer = 0
        #self.fps = FPSDisplay(self.window)

    def update(self, dt):

        #self.fps.draw()
        self.window.clear()
        self.frame_counter += 1
        # if size != (self.display.get_width() * 5, self.display.get_height() * 5):
        #    s = pg.Surface((self.display.get_width() * 5, self.display.get_height() * 5))
        #    size = (self.display.get_width() * 5, self.display.get_height() * 5

        for cords, room in room_objects.items():
            tiled_area = camera.repr_tiled_area()
            if cords[0] * rs.room_size[0] >= tiled_area[0] and cords[1] * rs.room_size[1] >= rs.room_size[1] >= \
                    tiled_area[1] or True:
                if not room.drawn:
                    room.tile_batch.draw()
                if not room.entities_drawn:
                    room.entity_batch.draw()

        # sub = s.subsurface(camera.centred_rectangle)
        # resized = pg.transform.smoothscale(sub, (self.display.get_width(), self.display.get_width()))
        # self.display.blit(resized, (0, -(self.display.get_width() - self.display.get_height()) / 2))
        # self.display.blit(camera.get_surface(scene), (0, 0))
        camera.update(dt)
        if not self.frame_counter % 1000:
            print(1 / dt)
            gc.collect()
            self.frame_counter = 1


def halt(self):
    self.halted.set()


class EventProcess:

    def __init__(self, manager):
        self.manager = manager
        self.speed = 4
        self.move = np.array([.0, .0, .0])

    def update(self, dt) -> None:
        global _escaped, events, known_rooms, entities, camera
        self.manager.set_camera_boundaries(camera.tiled_area)
        new = self.manager.get_rooms()

        camera.local_move_y(self.move[0])
        camera.local_move_x(self.move[1])
        camera.local_zoom(self.move[2])
        with lock:
            for k, v in new.items():
                if k not in known_rooms['known']:
                    room_objects[k] = Room(k, camera)
                    res = room_objects[k].update(v)
                else:
                    res = room_objects[k].update(v)
                if not res:
                    known_rooms['known'][k] = v

    def key_press(self, symbol, modifiers):
        if symbol == key.ESCAPE:
            pyg.app.exit()
        if symbol == key.W:
            self.move[0] = -1 * self.speed - 10 * int(key.MOD_SHIFT is modifiers)
        elif symbol == key.S:
            self.move[0] = 1 * self.speed + 10 * int(key.MOD_SHIFT is modifiers)
        if symbol == key.A:
            self.move[1] = -1 * self.speed - 10 * int(key.MOD_SHIFT is modifiers)
        elif symbol == key.D:
            self.move[1] = 1 * self.speed + 10 * int(key.MOD_SHIFT is modifiers)
        if symbol == key.R:
            self.move[2] = 0.005
        elif symbol == key.F:
            self.move[2] = -0.005

    def key_release(self, symbol, modifiers):
        if symbol is key.W:
            self.move[0] = 0
        elif symbol is key.S:
            self.move[0] = 0
        if symbol is key.A:
            self.move[1] = 0
        elif symbol is key.D:
            self.move[1] = 0
        if symbol is key.R:
            self.move[2] = 0
        elif symbol is key.F:
            self.move[2] = 0


class BaseScene:
    def __init__(self):
        self.tiles = {}
        self.entities = {}
        self.ui = {}
