import time

import pygame as pg
import pygame.math

import ui.game_objects as g_objects
from misc.ProjSettings import RenderingSettings as rs
from misc.ProjSettings import RoomSettings
import threading as thr
import math
import multiprocessing as mp

_escaped = False
events = {}
draw_requests = []
known_rooms = {}


def toFixed(numObj, digits=0):
    return float(f"{numObj:.{digits}f}")


class Camera(pg.Surface):
    def __init__(self):
        super(Camera, self).__init__(size=rs.resolution if rs.fullscreen else rs.window_size)
        self.position, self.velocity = pg.math.Vector3(0, 0, 1), pg.math.Vector3(0, 0, 0)
        self.d_position = pg.math.Vector3(0, 0, 0)
        self.friction = pg.math.Vector3(-.12, -.12, -.2)
        self.acceleration = pg.math.Vector3(0, 0, 0)
        self.max_velocity = pg.math.Vector3(1, 1, 1)
        self.max_position = pg.math.Vector3(100, 100, 3)

    def update(self, dt):
        self.movement(dt)
        self.acceleration.update()
        self.limit_velocity()

        self.position += self.velocity * dt + (self.acceleration * .5) * dt ** 2
        if self.position.x > self.max_position.x:
            self.position.x = self.max_position.x
        if self.position.y > self.max_position.y:
            self.position.y = self.max_position.y
        if self.position.z > self.max_position.z:
            self.position.z = self.max_position.z

    def local_move(self, x, y):
        self.acceleration.x = x / self.position.z
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
        if abs(self.velocity.x) < .01: self.velocity.x = 0
        if abs(self.velocity.y) < .01: self.velocity.y = 0
        if abs(self.velocity.z) < .01: self.velocity.z = 0

    def get_gridset(self):
        rect_cords = (int(math.ceil((self.position.x - (self.get_width() / self.position.z) / 2) / rs.room_size[0])),
                      int(math.ceil((self.position.y - (self.get_height() / self.position.z) / 2) / rs.room_size[1])),
                      int(math.ceil((self.position.x + (self.get_width() / self.position.z) / 2) / rs.room_size[0])),
                      int(math.ceil((self.position.x + (self.get_height() / self.position.z) / 2) / rs.room_size[1])))
        cords = []
        for x in range(rect_cords[0], rect_cords[2]):
            for y in range(rect_cords[1], rect_cords[3]):
                cords.append((x, y))
        return rect_cords, cords

    def get_surface(self, scene):
        rect_cords, cords = self.get_gridset()
        grid_surface = pg.Surface((100, 100))
        for c in cords:
            if c not in known_rooms:
                grid_surface.blit(c)

        return grid_surface



camera = Camera()
pg.init()


class DrawThread(thr.Thread):
    def __init__(self):
        super(DrawThread, self).__init__(daemon=True)
        self.clock = pg.time.Clock()
        if rs.fullscreen:
            self.display = pg.display.set_mode(size=(0, 0), flags=pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWACCEL)
        else:
            self.display = pg.display.set_mode(size=rs.window_size, flags=pg.RESIZABLE if rs.resizable else 0)
        self.rooms = dict()

    class DrawableRoomSukaBlyatb:
        def __init__(self, pos: tuple, tiles: dict):
            from misc.ProjSettings import TileSettings
            self.surf = pg.Surface((rs.room_size[0], rs.room_size[0]))
            self.surf.fill((50,0,100))
            self.pos = pos
            self.tiles = tiles

            for obj in tiles.keys():
                pygame.draw.rect(self.surf, (100, 100, 100), ((obj[0] * TileSettings.dimensions[0], obj[1] * TileSettings.dimensions[1]), TileSettings.dimensions))

        def get_figure_blyat(self, n):
            from misc.ProjSettings import TileSettings
            sf = pg.Surface((TileSettings.dimensions[0], TileSettings.dimensions[1]))
            sf.fill((50,0,100))
            match n:
                case 0:
                    return sf
                case 1:
                    sf.fill((100, 100, 100))
                    return sf
                case 2:
                    pygame.draw.polygon(sf, (100, 100, 100), [(0, 0), (sf.get_width(), sf.get_height()), (0, sf.get_height())])
                    return sf
                case 3:
                    pygame.draw.polygon(sf, (100, 100, 100),
                                        [(0, 0), (sf.get_width(), 0), (0, sf.get_height())])
                    return sf
                case 4:
                    pygame.draw.polygon(sf, (100, 100, 100),
                                        [(0, 0), (sf.get_width(), 0), (sf.get_width(), 0)])
                    return sf
                case 5:
                    pygame.draw.polygon(sf, (100, 100, 100),
                                        [(sf.get_width(), 0), (sf.get_width(), 0), (sf.get_width(), sf.get_height())])
                    return sf


        def update(self, tiles):
            self.tiles=tiles
            from misc.ProjSettings import TileSettings
            #print(tiles)
            for obj in tiles.keys():
                if (tiles[obj].__class__ is dict and "updated" in tiles[obj] and tiles[obj]["updated"]) or (tiles[obj].__class__ is not dict):
                    #pygame.draw.rect(self.surf, (50,0,100), ((obj[0] * TileSettings.dimensions[0], obj[1] * TileSettings.dimensions[1]), TileSettings.dimensions))
                    self.surf.blit(self.get_figure_blyat(tiles[obj]), ((obj[0] * TileSettings.dimensions[0], obj[1] * TileSettings.dimensions[1]), TileSettings.dimensions))

    def get_which_rooms_should_i_blit_in_this_current_situation(self):
        k_rooms = known_rooms
        rooms = []
        #print(camera.position)
        for i in range(int(camera.position[0]), self.display.get_width()//rs.room_size[0]):
            for j in range(int(camera.position[1]), self.display.get_height()//rs.room_size[1]):
                #print(i, j, k_rooms.keys())
                if (i, j) in k_rooms.keys():

                    rooms.append(((i, j), k_rooms[(i, j)]))
        return rooms

    def process_rooms(self):
        for room in self.get_which_rooms_should_i_blit_in_this_current_situation():

            if not room[0] in self.rooms.keys():
                self.rooms[room[0]] = DrawThread.DrawableRoomSukaBlyatb(room[0], room[1])
            else:
                self.rooms[room[0]].update(room[1])

            self.display.blit(self.rooms[room[0]].surf, (-camera.position[0]+rs.room_size[0] * room[0][0], -camera.position[1]+rs.room_size[1] * room[0][1]))

    def run(self):
        color = (0, 0, 0)
        scene = BaseScene()
        while not _escaped:
            tf = time.time()
            dt = self.clock.tick(rs.framerate) * .001 * rs.framerate
            camera.update(dt)

            self.display.fill(color)
            self.process_rooms()
            #print(self.rooms, self.get_which_rooms_should_i_blit_in_this_current_situation())

            pg.display.flip()
            print(1/(time.time()-tf))


class RenderThread(thr.Thread):
    def __init__(self, world):
        super(RenderThread, self).__init__(daemon=True, name='Antsy Rendering')
        self.clock = pg.time.Clock()
        self.world = world

    def run(self) -> None:
        global _escaped, events, known_rooms
        draw_thr = DrawThread()
        draw_thr.start()

        while not _escaped:

            for event in pg.event.get():
                events = pg.key.get_pressed()
                match event.type:
                    case pg.QUIT:
                        self.halt()
                if events[pg.K_w]:
                    camera.local_move(0, -.3)
                elif events[pg.K_s]:
                    camera.local_move(0, .3)
                if events[pg.K_a]:
                    camera.local_move(-.3, 0)
                elif events[pg.K_d]:
                    camera.local_move(.3, 0)
            known_rooms = self.world.get_rooms(camera.get_gridset()[1])

            self.clock.tick(rs.framerate // 2)

        draw_thr.join()

    def halt(self):
        global _escaped
        _escaped = True


class BaseScene:
    def __init__(self):
        self.tiles = {}
        self.entities = {}
        self.ui = {}
