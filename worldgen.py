import multiprocessing as mp
import threading as thr
import random as rn
from collections import ChainMap
import fastrand as frn
from misc import ProjSettings
from misc.ProjSettings import SimSettings
import _sha256
import tiles

_neighbors = lambda x, y, d: sum([int(d[x2, y2]) for x2 in range(x - 1, x + 2)
                                  for y2 in range(y - 1, y + 2)
                                  if (-1 < x < ProjSettings.RoomSettings.dimensions[0] and
                                      -1 < y < ProjSettings.RoomSettings.dimensions[1] and
                                      (x != x2 or y != y2) and
                                      (0 <= x2 < ProjSettings.RoomSettings.dimensions[0]) and
                                      (0 <= y2 < ProjSettings.RoomSettings.dimensions[1]))])


class _SmartDistributor:
    """
        Class for using a function over a pool of objects, similar to *map()* but executes only once on every call and
        can loop over the pool indefinitely; Use to distribute load over multiple processes/threads.
        Distributes load depending on how busy the pool is.
        **Not implemented.**
    """

    def __init__(self):
        raise NotImplemented


class SimpleDistributor:
    """
        Class for using a function over a pool of objects, similar to *map()* but executes only once on every call and
        can loop over the pool indefinitely; Use to distribute load over multiple processes/threads.
        Doesn't check if objects from a pool are ready to get a task, so they should have some kind of buffer.
    """

    def __init__(self, objects, func):
        self.objects = objects
        self.func = func
        self.pointer = 0

    def __call__(self, *args, **kwargs):
        if len(self.objects) == 0: return
        self.func(self.objects[self.pointer % len(self.objects)], *args, **kwargs)
        self.pointer += 1


class _WorldGen:
    """
        WorldGenerator, takes coordinates and seed to generate world using B678/S345678 Cellular Automata rule.
    """

    def __init__(self, room_options, seed, output):
        super().__init__()
        self.room_options = room_options
        self.width, self.height = self.room_options.dimensions
        self.seed = seed
        self.requests = mp.Queue()
        self.world = {}
        self.output = output

    def request(self, x: int, y: int, opts: ProjSettings.RoomSettings):
        """
            Request a room to be generated.

            :param x: Room's X coordinate
            :param y: Room's Y coordinate
            :param opts: Room's settings
        """
        self.requests.put((x, y, opts))

    def run(self) -> None:
        """
            Run the worker
        """
        w_seed = int.from_bytes(_sha256.sha256(str(self.seed).encode('utf-8')).digest(), 'little') // \
                 int.from_bytes(str(self.seed).encode('utf-8'), 'little')
        room_cords = [(x, y) for x in range(self.width) for y in range(self.height)]
        for request in iter(self.requests.get, None):
            room_seed = w_seed + request[0] * 10 + request[1]
            opts = request[2]
            frn.pcg32_seed(room_seed)
            generated_tiles = {cords: frn.pcg32bounded(2) for cords in room_cords}
            for _ in range(self.width * self.height // 5):
                for cords in room_cords:
                    c = _neighbors(cords[0], cords[1], generated_tiles)
                    if generated_tiles[cords] and c < 3:
                        generated_tiles[cords] = False
                        continue
                    if c >= 6:
                        generated_tiles[cords] = True

            tidy_tiles = {}

            for cords, tile in generated_tiles.items():
                tidy_tiles[cords] = tiles.RockTile(cords) if tile else tiles.EmptyTile(cords)
                if tile:
                    pass
            cords = (request[0], request[1])
            self.output.put((cords, tidy_tiles))


class _WorldGenThread(_WorldGen, thr.Thread):
    """
        Thread version of WorldGen class
    """

    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)


class _WorldGenProcess(_WorldGen, mp.Process):
    """
        Process version of WorldGen class
    """

    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)


class WorldGenHandler:
    """
        When called will return WorldGenHandlerThread or WorldGenHandlerProcess based on
        SimSettings.use_process_generation parameter
    """

    def __new__(cls, world_options):
        if SimSettings.use_process_generation:
            return WorldGenHandlerThread(world_options)
        else:
            return WorldGenHandlerProcess(world_options)


class _WorldGenHandler:
    """
        Base _WorldGenHandler class, distributes generation requests over the workers.
        Preferably use WorldGenHandler instead of this (_WorldGenHandler) class.
    """

    def __init__(self, world_options):
        self.requests = mp.Queue()
        self.output = mp.Queue()
        self.world_options = world_options
        self.room_options = ProjSettings.RoomSettings()
        self.seed = self.world_options.seed
        self.worker = _WorldGenProcess
        self.workers = []
        self.distributor = SimpleDistributor(self.workers, _WorldGen.request)

    def run(self) -> None:
        """
            Run the handler
        """
        self.workers = [self.worker(self.room_options, self.seed, self.output)
                        for _ in range(self.world_options.generator_processes)]
        self.distributor = SimpleDistributor(self.workers, _WorldGen.request)
        [worker.start() for worker in self.workers]
        [self.distributor(*request) for request in iter(self.requests.get, None)]
        [worker.requests.put(None) for worker in self.workers]
        [worker.join() for worker in self.workers]


class WorldGenHandlerProcess(_WorldGenHandler, mp.Process):
    """
        multiprocessing version of _WorldGenHandler
        Preferably use WorldGenHandler instead of this class.
    """

    def __init__(self, world_options):
        mp.Process.__init__(self)
        _WorldGenHandler.__init__(self, world_options)
        self.worker = _WorldGenThread


class WorldGenHandlerThread(_WorldGenHandler, thr.Thread):
    """
        threading version of _WorldGenHandler
        Preferably use WorldGenHandler instead of this class.
    """

    def __init__(self, world_options):
        thr.Thread.__init__(self)
        _WorldGenHandler.__init__(self, world_options)
