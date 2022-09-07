import threading as thr
from copy import copy
from math import ceil

import pygame as pg

import ui.game_objects as Objects
from misc.ProjSettings import RenderingSettings as rs
from ui.game_objects import Room

_escaped = False
events = {}
draw_requests = []
known_rooms = {'new': {}, 'known': {}}
room_objects = {}


def toFixed(numObj, digits=0):
    return float(f"{numObj:.{digits}f}")


class Camera(pg.Surface):
    def __init__(self):
        super(Camera, self).__init__(size=rs.resolution if rs.fullscreen else rs.window_size)
        self.position, self.velocity = pg.math.Vector3(1000, 1000, 1), pg.math.Vector3(0, 0, 0)
        self.d_position = pg.math.Vector3(0, 0, 0)
        self.friction = pg.math.Vector3(-.12, -.12, -.2)
        self.acceleration = pg.math.Vector3(0, 0, 0)
        self.max_velocity = pg.math.Vector3(1, 1, 1)
        self.max_position = pg.math.Vector3(4500, 4500, 6)
        self.min_position = pg.math.Vector3(0, 0, 0.45)

    def update(self, dt):
        self.movement(dt)
        self.acceleration.update()
        self.limit_velocity()

        if self.velocity.length() > 0:
            self.position += self.velocity * dt + (self.acceleration * .5) * dt ** 2
            self.position.x = min(self.position.x, self.max_position.x)
            self.position.y = min(self.position.y, self.max_position.y)
            self.position.z = min(self.position.z, self.max_position.z)
            self.position.x = max(self.position.x, self.min_position.x)
            self.position.y = max(self.position.y, self.min_position.y)
            self.position.z = max(self.position.z, self.min_position.z)

    @property
    def fov_rectangle(self):
        return pg.Rect(self.position.x - (self.get_width() * self.position.z / 2),
                       self.position.y - (self.get_height() * self.position.z / 2),
                       (self.get_width() * self.position.z),
                       (self.get_height() * self.position.z))

    @property
    def centred_rectangle(self):
        return (1000 - (self.get_width() * self.position.z / 2),
                       1000 - (self.get_height() * self.position.z / 2),
                       (self.get_width() * self.position.z),
                       (self.get_height() * self.position.z))

    @property
    def fod_rectangle(self):
        return pg.Rect(self.position.x - ((self.get_width() + 100 / self.position.z) * self.position.z / 2),
                       self.position.y - ((self.get_height() + 100 / self.position.z) * self.position.z / 2),
                       ((self.get_width() + 100 / self.position.z) * self.position.z),
                       ((self.get_height() + 100 / self.position.z) * self.position.z))

    @property
    def tiled_area(self):
        fod = self.fod_rectangle
        return (fod.topleft[0] // rs.room_size[0], fod.topleft[1] // rs.room_size[1],
                ceil(fod.bottomright[0] / rs.room_size[0]), ceil(fod.bottomright[1] / rs.room_size[1]))

    def repr_tiled_area(self):
        tr = self.tiled_area
        return pg.Rect(tr[0] * rs.room_size[0],
                       tr[1] * rs.room_size[1],
                       tr[2] * rs.room_size[0] - tr[0] * rs.room_size[0],
                       tr[3] * rs.room_size[1] - tr[1] * rs.room_size[1])

    def local_move_x(self, x):
        self.acceleration.x = x / self.position.z

    def local_move_y(self, y):
        self.acceleration.y = y / self.position.z

    def local_zoom(self, z):
        self.acceleration.z = z

    def movement(self, dt):
        self.acceleration.x += self.velocity.x * self.friction.x
        self.acceleration.y += self.velocity.y * self.friction.y
        self.acceleration.z += self.velocity.z * self.friction.z
        self.velocity.x += self.acceleration.x * dt
        self.velocity.y += self.acceleration.y * dt
        self.velocity.z += self.acceleration.z * dt

    def limit_velocity(self):
        self.velocity.x = max(-self.max_velocity.x, min(self.velocity.x, self.max_velocity.x))
        self.velocity.y = max(-self.max_velocity.y, min(self.velocity.y, self.max_velocity.y))
        self.velocity.z = max(-self.max_velocity.z, min(self.velocity.z, self.max_velocity.z))
        if abs(self.velocity.x) < .005: self.velocity.x = 0
        if abs(self.velocity.y) < .005: self.velocity.y = 0
        if abs(self.velocity.z) < .01: self.velocity.z = 0

    def get_cords(self):
        pass


camera = Camera()


class DrawThread(thr.Thread):
    def __init__(self):
        super(DrawThread, self).__init__()
        self.clock = pg.time.Clock()
        if rs.fullscreen:
            self.display = pg.display.set_mode(size=(0, 0), flags=pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWACCEL)
        else:
            self.display = pg.display.set_mode(size=rs.window_size, flags=pg.RESIZABLE if rs.resizable else 0)
        Objects.convert_images()

    def run(self):

        color = (0, 100, 0)
        scene = BaseScene()
        s = pg.Surface((6000, 6000))
        while not _escaped:
            dt = self.clock.tick(rs.framerate) * .001 * rs.framerate
            camera.update(dt)
            self.display.fill(color)
            s.fill((0, 0, 0))
            r_o = copy(room_objects)
            for cords, room in r_o.items():
                if camera.repr_tiled_area().collidepoint(cords[0] * rs.room_size[0], cords[1] * rs.room_size[1]):
                    room.draw(s, (cords[0] * rs.room_size[0], cords[1] * rs.room_size[1]), camera)
            sub = s.subsurface(camera.centred_rectangle)
            resized = pg.transform.smoothscale(sub, (self.display.get_width(), self.display.get_height()))
            self.display.blit(resized, (0, 0))
            # self.display.blit(camera.get_surface(scene), (0, 0))
            pg.display.flip()


class RenderThread(thr.Thread):
    def __init__(self, manager):
        super(RenderThread, self).__init__(name='Antsy Rendering')
        self.clock = pg.time.Clock()
        self.manager = manager
        pg.init()

    def run(self) -> None:
        global _escaped, events, known_rooms
        draw_thr = DrawThread()

        draw_thr.start()

        while not _escaped and not self.manager.halted.is_set():

            for event in pg.event.get():
                events = pg.key.get_pressed()
                match event.type:
                    case pg.QUIT:
                        self.halt()
                if events[pg.K_w]:
                    camera.local_move_y(-1)
                elif events[pg.K_s]:
                    camera.local_move_y(1)
                if events[pg.K_a]:
                    camera.local_move_x(-1)
                elif events[pg.K_d]:
                    camera.local_move_x(1)
                if events[pg.K_r]:
                    camera.local_zoom(0.025)
                elif events[pg.K_f]:
                    camera.local_zoom(-0.025)
            self.manager.set_camera_boundaries(camera.tiled_area)
            known_rooms['new'].update(self.manager.get_rooms())
            # print(known_rooms)
            for k, v in known_rooms['new'].items():
                if k not in known_rooms['known']:
                    room_objects[k] = Room()
                    res = room_objects[k].update(v)
                else:
                    res = room_objects[k].update(v)
                if not res:
                    known_rooms['known'][k] = v

            self.clock.tick(rs.framerate // 2)
        self.halt()
        draw_thr.join()
        pg.display.quit()
        pg.quit()

    def halt(self):
        global _escaped
        _escaped = True
        self.manager.halted.set()


class BaseScene:
    def __init__(self):
        self.tiles = {}
        self.entities = {}
        self.ui = {}
