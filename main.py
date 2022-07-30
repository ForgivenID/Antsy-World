import time

from world import *
import multiprocessing as mp
from threading import Thread
from queue import Queue as Queue
from worldgen import WorldGenHandler
import gc


class LogicProcess(mp.Process):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    mp.current_process().name = "Antsy World"
    wgh = WorldGenHandler(ProjSettings.WorldSettings())
    [[wgh.request(x, y, ProjSettings.RoomSettings()) for x in range(10)] for y in range(10)]
    time1 = time.time()
    wgh.start()
    # from ui.rendering import Renderer
    # renderer = Renderer()
    boolmap = {}
    i = 0
    for _ in range(100):
        i += 1
        res = wgh.output.get()
        room_cords = res[0]
        for local_cords, tile in res[1].items():
            tile_cords = (local_cords[0] + ProjSettings.RoomSettings.dimensions[0] * room_cords[0],
                          local_cords[1] + ProjSettings.RoomSettings.dimensions[1] * room_cords[1])
            boolmap[tile_cords] = bool(tile)
        if not i % 10:
            print(i / 100)
            if not i % 100:
                gc.collect()
    time2 = time.time()
    print('done, --', time2 - time1)
    [[wgh.request(x, y, ProjSettings.RoomSettings()) for x in range(10)] for y in range(10)]
    time1 = time.time()
    # from ui.rendering import Renderer
    # renderer = Renderer()
    i = 0
    correct = 0
    boolmap2 = {}
    for _ in range(100):
        i += 1
        res = wgh.output.get()
        room_cords = res[0]
        for local_cords, tile in res[1].items():
            tile_cords = (local_cords[0] + ProjSettings.RoomSettings.dimensions[0] * room_cords[0],
                          local_cords[1] + ProjSettings.RoomSettings.dimensions[1] * room_cords[1])
            if boolmap[tile_cords] == bool(tile):
                correct += 1
            boolmap2[tile_cords] = bool(tile)
        if not i % 10:
            print(i / 100, 'errors:', (len(boolmap2) - correct) / 100)
            if not i % 100:
                gc.collect()
    time2 = time.time()
    print('done, --', time2 - time1)
    wgh.halt()
    print(len(boolmap))
    import pygame

    surface = pygame.Surface((1000, 1000))
    pixmap = pygame.pixelarray.PixelArray(surface)
    running = True
    [pixmap.surface.set_at(cords, (100, 100, 100) if tile else (0, 0, 0)) for cords, tile in boolmap.items()]
    del pixmap
    pygame.init()
    display = pygame.display.set_mode((1000, 1000))
    display.blit(surface, (0, 0))
    pygame.display.flip()
    pixmap = pygame.pixelarray.PixelArray(surface)
    time.sleep(1)
    [pixmap.surface.set_at((cords[0] + 150, cords[1]), (100, 100, 100) if tile else (0, 0, 0))
     for cords, tile in boolmap2.items()]
    time.sleep(1)
    [pixmap.surface.set_at((cords[0] + 300, cords[1]), (0, 100, 0) if tile == boolmap[cords] else (100, 0, 0))
     for cords, tile in boolmap2.items()]
    del pixmap
    display.fill((0, 0, 0))
    scaled_surface = pygame.Surface((400, 400))
    surface = pygame.transform.scale(surface, (1500, 1500))
    display.blit(surface, (0, 0))
    pygame.display.flip()
    pixmap = pygame.pixelarray.PixelArray(surface)
    while running:
        for event in pygame.event.get():
            if event is pygame.QUIT:
                wgh.join()
                running = False
    wgh.join()
