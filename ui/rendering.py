import gc
import multiprocessing
import threading as thr
import time
from math import ceil
from threading import RLock

import numpy as np
import pygame as pg

import ui.game_objects as Objects
from misc.ProjSettings import RenderingSettings as rs
from ui.game_objects import Room

_escaped = False
events = {}
known_rooms = {'new': {}, 'known': {}}
room_objects = {}
entities = []
picked_position: tuple[int, int] = (0, 0)

pg.font.init()
font = pg.font.SysFont("Comic Sans Ms", 36)

lock = RLock()


class Camera(pg.Surface):
    """
        Camera object class, calculates camera position and FOV & FOD boundaries.
    """

    def __init__(self):
        super(Camera, self).__init__(size=(600, 600))
        self.position, self.velocity = np.array([1000., 1000., 1.], ), np.array([.0, .0, .0])
        self.d_position = np.array([.0, .0, .0])
        self.friction = np.array([-.03, -.03, -.05])
        self.acceleration = np.array([.0, .0, .0])
        self.max_velocity = np.array([6., 6., 1.])
        self.max_position = np.array([18000., 18000., 5])
        self.min_position = np.array([0., 0., 0.7])

    def movement(self, dt):
        """
        Perform movement.
        :param dt: delta time, seconds
        """
        self.acceleration += self.velocity * self.friction
        self.velocity += (self.acceleration * dt)

    def limit_velocity(self):
        """
        Bound velocity values to max or min values.
        """
        for i, val in enumerate(self.velocity):
            if val > self.max_velocity[i]:
                self.velocity[i] = self.max_velocity[i]
        if abs(self.velocity[0]) < .005:
            self.velocity[0] = 0
        if abs(self.velocity[1]) < .005:
            self.velocity[1] = 0
        if abs(self.velocity[2]) < .002:
            self.velocity[2] = 0

    def update(self, dt):
        """
        Update camera's position
        :param dt: delta time, seconds
        """
        self.movement(dt)
        self.acceleration *= 0
        self.limit_velocity()
        if sum(map(np.square, self.velocity)) > 0:
            self.position += self.velocity * dt + (self.acceleration * .5) * dt ** 2
            for i, val in enumerate(self.position):
                if val > self.max_position[i]:
                    self.position[i] = self.max_position[i]
            for i, val in enumerate(self.position):
                if val < self.min_position[i]:
                    self.position[i] = self.min_position[i]

    @property
    def fov_rectangle(self) -> pg.Rect:
        """
        Calculate Field Of View rectangle

        :return: fov pygame.Rect
        """
        return pg.Rect(self.position[0] - (self.get_width() * self.position[2] / 2),
                       self.position[1] - (self.get_height() * self.position[2] / 2),
                       (self.get_width() * self.position[2]),
                       (self.get_height() * self.position[2]))

    @property
    def centred_rectangle(self) -> tuple[float, float, float, float]:
        """
        Calculate local camera boundaries

        :return: tuple[x, y, w, h]
        """
        return (3000 - (self.get_width() * self.position[2] / 2),
                3000 - (self.get_height() * self.position[2] / 2),
                (self.get_width() * self.position[2]),
                (self.get_height() * self.position[2]))

    @property
    def fod_rectangle(self) -> pg.Rect:
        """
        Return Field Of Draw rectangle

        :return: fod pygame.Rect
        """
        return pg.Rect(self.position[0] - ((self.get_width() + 100 / self.position[2]) * self.position[2] / 2),
                       self.position[1] - ((self.get_height() + 100 / self.position[2]) * self.position[2] / 2),
                       ((self.get_width() + 100 / self.position[2]) * self.position[2]),
                       ((self.get_height() + 100 / self.position[2]) * self.position[2]))

    @property
    def tiled_area(self) -> tuple[float, float, float, float]:
        """
        Return FOD bound to Room grid.
        May be taken as a Rect containing all Rooms colliding with FOD rectangle

        :return: tuple[x1, y1, x2, y2] (Room grid coordinates)
        """
        fod = self.fod_rectangle
        return (int(fod.topleft[0] // rs.room_size[0]), int(fod.topleft[1] // rs.room_size[1]),
                ceil(fod.bottomright[0] / rs.room_size[0]), ceil(fod.bottomright[1] / rs.room_size[1]))

    def repr_tiled_area(self) -> pg.Rect:
        """
        Return FOD bound to Room grid.
        May be taken as a Rect containing all Rooms colliding with FOD rectangle

        :return: pygame.Rect (Global coordinates)
        """
        tr = self.tiled_area
        return pg.Rect(tr[0] * rs.room_size[0],
                       tr[1] * rs.room_size[1],
                       tr[2] * rs.room_size[0] - tr[0] * rs.room_size[0],
                       tr[3] * rs.room_size[1] - tr[1] * rs.room_size[1])

    def local_move_x(self, x):
        """
        accelerate on x axis

        :param x: Newtons
        """
        self.acceleration[0] = x / self.position[2]

    def local_move_y(self, y):
        """
        accelerate on y axis

        :param y: Newtons
        """
        self.acceleration[1] = y / self.position[2]

    def local_zoom(self, z):
        """
        accelerate on z axis

        :param z: Newtons
        """
        self.acceleration[2] = z / self.position[2]


camera = Camera()


class DrawThread(thr.Thread):
    """
        Drawing thread.
    """

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
        """
        Run this DrawingThread.
        """
        tiled = camera.repr_tiled_area()
        s = pg.Surface(tiled.size)
        se = pg.Surface(tiled.size)
        pg.event.pump()
        frame_counter = 0
        avg_fps: str = '000'
        rpf: str = '000/000'
        frametime_buffer: int = 0
        self.display.set_alpha(None)
        fps_text = font.render(avg_fps, True, (255, 0, 0))
        rpf_text = font.render(rpf, True, (255, 0, 0))
        redraw: bool = False
        room_per_frame: int = 0
        entity_redraw_per_frame: int = 0
        while not self.halted.is_set():
            frame_counter += 1
            last_frame_took = self.clock.tick(rs.framerate) * .001
            dt = last_frame_took * rs.framerate
            camera.update(dt)
            fov = camera.fov_rectangle
            tiled = camera.repr_tiled_area()
            if s.get_rect().size != tiled.size:
                del s
                s = pg.Surface(tiled.size)
                s.set_colorkey(None)
                del se
                se = pg.Surface(tiled.size)
                redraw = True
            with lock:
                for cords, room in room_objects.items():
                    if redraw:
                        room.drawn = False
                        room.entities_drawn = False
                    if tiled.collidepoint(cords[0] * rs.room_size[0], cords[1] * rs.room_size[1]):
                        if not room.drawn:
                            room.draw_tiles(s, ((cords[0] * rs.room_size[0] - tiled.left),
                                                (cords[1] * rs.room_size[1] - tiled.top)))
                            room_per_frame += 1
                        if not room.entities_drawn:
                            room.draw_entities(se, ((cords[0] * rs.room_size[0] - tiled.left),
                                                    (cords[1] * rs.room_size[1] - tiled.top)))
                            entity_redraw_per_frame += 1
            redraw = False

            sub = s.subsurface(((fov.left - tiled.left), (fov.top - tiled.top), *fov.size))
            sube = se.subsurface(((fov.left - tiled.left), (fov.top - tiled.top), *fov.size))
            if camera.position[2] < 1.25:
                resized = pg.transform.scale(sub, (self.display.get_width(), self.display.get_width()))
            else:
                resized = pg.transform.smoothscale(sub, (self.display.get_width(), self.display.get_width()))
            resizede = pg.transform.scale(sube, (self.display.get_width(), self.display.get_width()))
            resizede.set_colorkey((0, 0, 0))
            self.display.blit(resized, (0, 0))
            # self.display.blit(camera.get_surface(scene), (0, 0))
            frametime_buffer += last_frame_took
            if not frame_counter % 100:
                avg_frametime = frametime_buffer / 100
                avg_fps = str(round(1 / avg_frametime, 1))
                frametime_buffer = 0
                rpf = str(round(room_per_frame / 100, 2)) + '/' + str(round(entity_redraw_per_frame / 100, 2))
                fps_text = font.render(avg_fps, True, (255, 0, 0))
                rpf_text = font.render(rpf, True, (255, 0, 0))
                room_per_frame = 0
                entity_redraw_per_frame = 0
                if not frame_counter % 700:
                    gc.collect()

            self.display.blits([(resized, resized.get_rect(topleft=(0, 0))),
                                (resizede, resized.get_rect(topleft=(0, 0))),
                                (fps_text, fps_text.get_rect(topleft=(0, 0))),
                                (rpf_text, fps_text.get_rect(bottomleft=(0, self.display.get_height())))])
            pg.display.flip()

    def halt(self):
        """
        Stop this thread.
        """
        self.halted.set()


class RenderThread(multiprocessing.Process):
    """
        Rendering thread. Processes events and drawing.
    """

    def __init__(self, manager):
        super(RenderThread, self).__init__(name='Antsy Rendering', daemon=True)
        self.manager = manager
        pg.init()

    def run(self) -> None:
        """
        Run this RenderingThread.
        """
        global _escaped, events, known_rooms, entities, picked_position
        draw_thr = DrawThread()

        draw_thr.start()
        pg.display.set_caption('AntsyWorld')
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN])
        speed = 0.5
        shift = False

        while not _escaped and not self.manager.halted.is_set():

            for event in pg.event.get():
                events = pg.key.get_pressed()

                match event.type:
                    case pg.QUIT:
                        self.manager.halted.set()
                        self.halt()
                    case pg.MOUSEBUTTONDOWN:
                        pass
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
            tiled = camera.repr_tiled_area()
            with lock:
                for k, v in new.items():
                    if k not in known_rooms['known']:
                        room_objects[k] = Room()
                        res = room_objects[k].update(v)
                    elif tiled.collidepoint(k[0] * rs.room_size[0], k[1] * rs.room_size[1]):
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
        """
        Stop this thread.
        """
        global _escaped
        _escaped = True
        self.manager.halted.set()


class BaseScene:
    def __init__(self):
        self.tiles = {}
        self.entities = {}
        self.ui = {}
