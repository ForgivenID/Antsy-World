import gc
import multiprocessing
import threading as thr
import time
from math import ceil

import pygame as pg

import ui.game_objects as Objects
from misc.ProjSettings import RenderingSettings as rs
from ui.game_objects import Room

_escaped = False
events = {}
known_rooms = {'new': {}, 'known': {}}
room_objects = {}
entities = []

pg.font.init()
font = pg.font.SysFont("Comic Sans Ms", 36)

from threading import RLock

lock = RLock()


def toFixed(numObj, digits=0):
    return float(f"{numObj:.{digits}f}")


class Camera(pg.Surface):
    def __init__(self):
        super(Camera, self).__init__(size=rs.window_size)
        self.position, self.velocity = pg.math.Vector3(3000, 3000, 1), pg.math.Vector3(0, 0, 0)
        self.d_position = pg.math.Vector3(0, 0, 0)
        self.friction = pg.math.Vector3(-.12, -.12, -.2)
        self.acceleration = pg.math.Vector3(0, 0, 0)
        self.max_velocity = pg.math.Vector3(4, 4, 1)
        self.max_position = pg.math.Vector3(18000, 18000, 5)
        self.min_position = pg.math.Vector3(0, 0, 0.5)

    def movement(self, dt):
        self.acceleration += pg.math.Vector3(self.velocity.elementwise() * self.friction.elementwise())
        self.velocity += (self.acceleration * dt)

    def limit_velocity(self):
        if self.velocity.length() > self.max_velocity.x:
            self.velocity = self.velocity.normalize() * self.max_velocity.x
        if abs(self.velocity.x) < .005: self.velocity.x = 0
        if abs(self.velocity.y) < .005: self.velocity.y = 0
        if abs(self.velocity.z) < .002: self.velocity.z = 0

    def update(self, dt):
        self.movement(dt)
        self.acceleration.update()
        self.limit_velocity()

        if self.velocity.length() > 0:
            self.position += self.velocity * dt + (self.acceleration * .5) * dt ** 2
            if self.position.length() > self.max_position.x:
                self.position = self.position.normalize() * self.max_position.x
            if self.position.length() < self.min_position.x:
                self.position = self.position.normalize() * self.min_position.x

    @property
    def fov_rectangle(self):
        return pg.Rect(self.position.x - (self.get_width() * self.position.z / 2),
                       self.position.y - (self.get_height() * self.position.z / 2),
                       (self.get_width() * self.position.z),
                       (self.get_height() * self.position.z))

    @property
    def centred_rectangle(self):
        return (3000 - (self.get_width() * self.position.z / 2),
                3000 - (self.get_height() * self.position.z / 2),
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
        return (int(fod.topleft[0] // rs.room_size[0]), int(fod.topleft[1] // rs.room_size[1]),
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
        self.acceleration.z = z / self.position.z

    def get_cords(self):
        pass


camera = Camera()


class DrawThread(thr.Thread):
    def __init__(self):
        super(DrawThread, self).__init__(name='Antsy Drawer', daemon=True)
        self.clock = pg.time.Clock()
        if rs.fullscreen:
            self.display = pg.display.set_mode(size=(0, 0), flags=pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWACCEL)
        else:
            self.display = pg.display.set_mode(size=rs.window_size, flags=pg.RESIZABLE if rs.resizable else 0)
        Objects.convert_images()
        self.halted = thr.Event()

    def run(self):

        s = pg.Surface((6000, 6000))
        size = (0, 0)
        pg.event.pump()
        frame_counter = 0
        avg_fps = '000'
        rpf = '000'
        frametime_buffer = 0
        self.display.set_alpha(None)
        fps_text = font.render(avg_fps, True, (255, 0, 0))
        rpf_text = font.render(rpf, True, (255, 0, 0))
        while not self.halted.is_set():
            room_per_frame = 0
            frame_counter += 1
            if size != (self.display.get_width() * 5, self.display.get_height() * 5):
                s = pg.Surface((self.display.get_width() * 5, self.display.get_height() * 5))
                size = (self.display.get_width() * 5, self.display.get_height() * 5)
            last_frame_took = self.clock.tick(rs.framerate) * .001
            dt = last_frame_took * rs.framerate
            camera.update(dt)

            with lock:
                for cords, room in room_objects.items():
                    if camera.repr_tiled_area().collidepoint(cords[0] * rs.room_size[0],
                                                             cords[1] * rs.room_size[1]):
                        if not room.drawn:
                            room.draw_tiles(s, (cords[0] * rs.room_size[0],
                                                cords[1] * rs.room_size[1]), camera)
                        if not room.entities_drawn:
                            room.draw_entities(s, (cords[0] * rs.room_size[0],
                                                   cords[1] * rs.room_size[1]), camera)
                        room_per_frame += 1

            sub = s.subsurface(camera.centred_rectangle)
            resized = pg.transform.smoothscale(sub, (self.display.get_width(), self.display.get_width()))
            self.display.blit(resized, (0, -(self.display.get_width() - self.display.get_height()) / 2))
            # self.display.blit(camera.get_surface(scene), (0, 0))
            frametime_buffer += last_frame_took

            if not frame_counter % 100:
                avg_frametime = frametime_buffer / 100
                avg_fps = str(round(1 / avg_frametime, 1))
                frametime_buffer = 0
                rpf = str(room_per_frame)
                fps_text = font.render(avg_fps, True, (255, 0, 0))
                rpf_text = font.render(rpf, True, (255, 0, 0))

                if not frame_counter % 1000:
                    gc.collect()

            self.display.blits([(fps_text, fps_text.get_rect(topleft=(0, 0))),
                                (rpf_text, fps_text.get_rect(bottomleft=(0, self.display.get_height())))])
            pg.display.flip()

    def halt(self):
        self.halted.set()


class RenderThread(multiprocessing.Process):
    """

    """

    def __init__(self, manager):
        super(RenderThread, self).__init__(name='Antsy Rendering', daemon=True)
        self.manager = manager
        pg.init()

    def run(self) -> None:
        global _escaped, events, known_rooms, entities
        draw_thr = DrawThread()

        draw_thr.start()
        pg.display.set_caption('AntsyWorld')
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP])
        speed = 0.5
        shift = False

        while not _escaped and not self.manager.halted.is_set():

            for event in pg.event.get():
                events = pg.key.get_pressed()

                match event.type:
                    case pg.QUIT:
                        self.manager.halted.set()
                        self.halt()
                if events[pg.K_ESCAPE]:
                    self.manager.halted.set()
                    self.halt()
                if events[pg.K_w]:
                    camera.local_move_y(-1 * speed - 10 * shift)
                elif events[pg.K_s]:
                    camera.local_move_y(1 * speed + 10 * shift)
                if events[pg.K_a]:
                    camera.local_move_x(-1 * speed - 10 * shift)
                elif events[pg.K_d]:
                    camera.local_move_x(1 * speed + 10 * shift)
                if events[pg.K_r]:
                    camera.local_zoom(0.005)
                elif events[pg.K_f]:
                    camera.local_zoom(-0.005)
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        shift = not shift

            self.manager.set_camera_boundaries(camera.tiled_area)
            new = self.manager.get_rooms()

            with lock:
                for k, v in new.items():
                    if k not in known_rooms['known']:
                        room_objects[k] = Room()
                        res = room_objects[k].update(v)
                    else:
                        res = room_objects[k].update(v)
                    if not res:
                        known_rooms['known'][k] = v
            time.sleep(1 / (rs.framerate / 3))

        self.halt()
        draw_thr.halt()
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
