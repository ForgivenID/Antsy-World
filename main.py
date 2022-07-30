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
    dim = 20
    [[wgh.request(x, y, ProjSettings.RoomSettings()) for x in range(dim)] for y in range(dim)]
    wgh.start()
    # from ui.rendering import Renderer
    # renderer = Renderer()
    boolmap = {}
    i = 0
    time1 = time.time()
    for _ in range(dim**2):
        i += 1
        res = wgh.output.get()
        room_cords = res[0]
        for local_cords, tile in res[1].items():
            tile_cords = (local_cords[0] + ProjSettings.RoomSettings.dimensions[0] * room_cords[0],
                          local_cords[1] + ProjSettings.RoomSettings.dimensions[1] * room_cords[1])
            boolmap[tile_cords] = bool(tile)
        if not i % (dim//10):
            print(f'{(i / dim**2) * 100}%')
            if not i % 100:
                gc.collect()
    time2 = time.time()
    print(f'done, -- {time2-time1} sec,\n{1000*(time2 - time1)/dim**2} millis per chunk')
    print(f'chunk dimensions: {ProjSettings.RoomSettings.dimensions[0]}x{ProjSettings.RoomSettings.dimensions[1]}')
    print(f'chunks generated: {dim**2}')
    wgh.halt()
    print(len(boolmap))
    import pygame

    surface = pygame.Surface((1000, 1000))
    pixmap = pygame.pixelarray.PixelArray(surface)
    running = True
    [pixmap.surface.set_at((cords[0]*2, cords[1]*2), (100, 100, 100) if tile else (0, 0, 0)) for cords, tile in boolmap.items()]
    del pixmap
    pygame.init()
    display = pygame.display.set_mode((1000, 1000))
    display.blit(surface, (0, 0))
    pygame.display.flip()
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event is pygame.QUIT:
                running = False
        clock.tick(25)
    wgh.join()
