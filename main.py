from world import *
# import ursina
import multiprocessing as mp
from threading import Thread
from queue import Queue as Queue

from worldgen import WorldGenHandler


class LogicProcess(mp.Process):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    wgh = WorldGenHandler(ProjSettings.WorldSettings())
    [[wgh.requests.put((x, y, ProjSettings.RoomSettings())) for x in range(10)] for y in range(10)]
    wgh.start()
    for _ in range(100):
        matrix = [['' for _ in range(25)] for _ in range(25)]
        res = wgh.output.get()
        for cords, tile in res[1].items():
            matrix[cords[0]][cords[1]] = ' ' if type(tile) is EmptyTile else '#'
        print('\n'.join([' '.join(row) for row in matrix]))
        print('--')

