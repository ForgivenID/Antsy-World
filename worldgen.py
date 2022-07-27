import multiprocessing as mp
import threading as thr
import random as rn
from collections import ChainMap

from misc import ProjSettings
from misc.ProjSettings import SimSettings
import _sha256
import tiles


class SmartDistributor:
    def __init__(self):
        raise NotImplemented


class SimpleDistributor:
    def __init__(self, objects, func):
        self.objects = objects
        self.func = func
        self.pointer = 0

    def __call__(self, *args, **kwargs):
        if len(self.objects) == 0: return
        self.func(self.objects[self.pointer % len(self.objects)], *args, **kwargs)
        self.pointer += 1


class WorldGen:
    def __init__(self, room_options, seed, output):
        super().__init__()
        self.room_options = room_options
        self.width, self.height = self.room_options.dimensions
        self.seed = seed
        self.requests = mp.Queue()
        self.output = output
        self.neighbors = lambda x, y, d: sum([int(d[x2, y2]) for x2 in range(x - 1, x + 2)
                                              for y2 in range(y - 1, y + 2)
                                              if (-1 < x < self.width and
                                                  -1 < y < self.height and
                                                  (x != x2 or y != y2) and
                                                  (0 <= x2 < self.width) and
                                                  (0 <= y2 < self.height))])

    def generate(self, x, y, opts):
        self.requests.put((x, y, opts))


class WorldGenThread(WorldGen, thr.Thread):
    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)

    def run(self) -> None:
        for request in iter(self.requests.get, None):
            room_seed = _sha256.sha256(str(self.seed).encode('utf-8')).hexdigest() + \
                        _sha256.sha256((str(request[0]) + str(request[1])).encode('utf-8')).hexdigest()
            opts = request[2]
            random = rn.Random(room_seed)
            generated_tiles = dict(ChainMap(*[{(x, y): bool(random.randint(0, 1))
                                          for x in range(self.width)} for y in range(self.height)]))
            for _ in range(self.width * self.height // 5):
                for x in range(self.width):
                    for y in range(self.height):
                        c = self.neighbors(x, y, generated_tiles)
                        if generated_tiles[(x, y)] and c < 3:
                            generated_tiles[(x, y)] = False
                            continue
                        if c >= 6:
                            generated_tiles[(x, y)] = True

            tidy_tiles = {}

            for cords, tile in generated_tiles.items():
                tidy_tiles[cords] = tiles.RockTile(cords) if tile else tiles.EmptyTile(cords)
                if tile:
                    pass
            cords = (request[0], request[1])
            self.output.put((cords, tidy_tiles))


class WorldGenProcess(WorldGen, mp.Process):
    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)

    def run(self) -> None:
        for request in iter(self.requests.get, None):
            room_seed = _sha256.sha256(str(self.seed).encode('utf-8')).hexdigest() + \
                        _sha256.sha256((str(request[0]) + str(request[1])).encode('utf-8')).hexdigest()
            opts = request[2]
            random = rn.Random(room_seed)
            generated_tiles = ChainMap(*[{(x, y): bool(random.randint(0, 1))
                               for x in range(self.width)} for y in range(self.height)])
            for _ in range(self.width * self.height // 6):
                for x in range(self.width):
                    for y in range(self.height):
                        c = self.neighbors(x, y, generated_tiles)
                        if generated_tiles[(x, y)] and c < 3:
                            generated_tiles[(x, y)] = False
                            continue
                        if c >= 6:
                            generated_tiles[(x, y)] = True

            tidy_tiles = {}

            for cords, tile in generated_tiles.items():
                tidy_tiles[cords] = tiles.RockTile(cords) if tile else tiles.EmptyTile(cords)
                if tile:
                    pass
            cords = (request[0], request[1])
            self.output.put((cords, tidy_tiles))



class WorldGenHandler(mp.Process):
    def __init__(self, world_options):
        super(WorldGenHandler, self).__init__(daemon=True)

        self.requests = mp.Queue()
        self.output = mp.Queue()

        self.world_options = world_options
        self.room_options = ProjSettings.RoomSettings()
        self.seed = self.world_options.seed

        self.worker = WorldGenThread
        if SimSettings.use_process_generation:
            self.worker = WorldGenProcess

        self.workers = []

        self.distributor = SimpleDistributor(self.workers, WorldGen.generate)

    def run(self) -> None:
        self.workers = [self.worker(self.room_options, self.seed, self.output)
                        for _ in range(self.world_options.generator_processes)]
        self.distributor = SimpleDistributor(self.workers, WorldGen.generate)
        [worker.start() for worker in self.workers]
        [self.distributor(*request) for request in iter(self.requests.get, None)]
        [worker.requests.put(None) for worker in self.workers]
        [worker.join() for worker in self.workers]