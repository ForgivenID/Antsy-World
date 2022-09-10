import copy
import gc
import hashlib
import multiprocessing as mp
import random as rnd
import threading as thr
from functools import cache, lru_cache

from misc import ProjSettings
from misc.ProjSettings import SimSettings

shape_patterns = {

    (1, 1, 1, 1): (1, 0),  # Full wall

    (0, 1, 0, 1): (2, 0),  # Wedge wall
    (1, 1, 0, 0): (2, 1),
    (1, 0, 1, 0): (2, 2),
    (0, 0, 1, 1): (2, 3),

    (1, 1, 0, 1): (3, 0),  # Sided wall
    (1, 1, 1, 0): (3, 1),
    (1, 0, 1, 1): (3, 2),
    (0, 1, 1, 1): (3, 3),

    (0, 1, 1, 0): (4, 0),  # Tube wall
    (1, 0, 0, 1): (4, 1),

    (0, 1, 0, 0): (5, 0),  # Pointy wall
    (1, 0, 0, 0): (5, 1),
    (0, 0, 1, 0): (5, 2),
    (0, 0, 0, 1): (5, 3),

    (0, 0, 0, 0): (6, 0),  # Round pillar wall

}


def _neighbors(x, y, d, bx=ProjSettings.RoomSettings.dimensions[0], by=ProjSettings.RoomSettings.dimensions[1]):
    i = 0
    for x2 in range(x - 1, x + 2):
        for y2 in range(y - 1, y + 2):
            if (x != x2 or y != y2) and -1 < x < bx and -1 < y < by and (0 <= x2 < bx) and (0 <= y2 < by):
                if d[x2, y2]:
                    i += 1
    return i


@lru_cache(maxsize=120)
def _room_neighbors(x, y):
    output = {}
    nr = _n_room_neighbors()
    for i, cords in nr.items():
        output[i] = (cords[0] + x * ProjSettings.RoomSettings.dimensions[0],
                     cords[1] + y * ProjSettings.RoomSettings.dimensions[1])

    return output


@cache
def _n_room_neighbors():
    output = {}
    i = 0
    for x2 in range(-1, 2):
        for y2 in range(-1, 2):
            i += 1
            if not i % 2:
                output[i] = (x2, y2)
    return output


def check_shape(x, y, d):
    neighbors = [bool(d[cords[0] + x, cords[1] + y]) if cords in d else False for i, cords in
                 _n_room_neighbors().items()]
    return shape_patterns[tuple(neighbors)] if tuple(neighbors) in shape_patterns else (1, 0)


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
        self.halted = mp.Event()
        self.room_options = room_options
        self.width, self.height = self.room_options.dimensions
        self.seed = seed
        self.requests = mp.Queue()
        self.world = {}
        self.output = output
        self.room_cords = [(x, y) for x in range(self.width) for y in range(self.height)]
        self.n_room_cords = copy.copy(self.room_cords)
        self.n_room_cords.extend(
            [(cords[0] + offset_x * self.width // 2, cords[1] + offset_y * self.height // 2)
             for cords in self.room_cords for offset_x in range(3) for offset_y in range(3) if
             (cords[0] + offset_x * self.width // 2, cords[1] + offset_y * self.height // 2) not in self.room_cords])
        self.generated = []

    def request(self, x: int, y: int):
        """
            Request a room to be generated.

            :param x: Room's X coordinate
            :param y: Room's Y coordinate
            :param opts: Room's settings
        """
        self.requests.put((x, y))

    @lru_cache(maxsize=20)
    def generate_noise(self, room_seed, offset_x=0, offset_y=0):
        """
            Generate noise from seed

        :param room_seed: Room's seed
        :param offset_x: Room's offset by X
        :param offset_y: Room's offset by Y
        :return: Generated noise (dict)
        """
        random = rnd.Random(room_seed)
        return {(cords[0] + offset_x * self.width, cords[1] + offset_y * self.height): bool(random.randint(0, 1))
                for cords in self.room_cords}

    @lru_cache(maxsize=200)
    def generate_room_seed(self, w_seed, cords):
        return ((cords[0] + 1) << 256 + (cords[1] * ProjSettings.WorldSettings.dimensions[0] + 1) << 128) ^ w_seed

    def generate(self, w_seed, cords, f=True):
        """
            Generate cave-like 2D structure based of world seed and it's coordinates

        :param w_seed: World's seed
        :param cords: Room's coordinates
        :return: Generated structure (dict)
        """
        if cords[0] < 0 or cords[1] < 0:
            return {cords: {}}
        rn = _room_neighbors(cords[0], cords[1])
        local_rn = _n_room_neighbors()
        # random = rnd.Random(w_seed)
        # [random.random() for _ in range(cords[0] + cords[1] * self.width)]
        room_seed = self.generate_room_seed(w_seed, cords)
        generated_tiles = self.generate_noise(room_seed)
        random = rnd.Random(room_seed)
        for i, c in rn.items():
            l_room_seed = self.generate_room_seed(w_seed, c)
            generated_tiles.update(self.generate_noise(l_room_seed,
                                                       offset_x=local_rn[i][0],
                                                       offset_y=local_rn[i][1]))
        for _ in range(6):
            for _cords in generated_tiles.keys():
                c = _neighbors(_cords[0], _cords[1], generated_tiles)
                if generated_tiles[_cords] and c < 3:
                    generated_tiles[_cords] = 0
                    continue
                elif c >= 6:
                    generated_tiles[_cords] = 1

        return {
            'tiles': {
                cords: {'type': check_shape(*cords, generated_tiles), 'object': 'NormalWall'} if tile else
                {'type': 1, 'object': 'NormalFloor'}
                for cords, tile in generated_tiles.items() if cords in self.room_cords}}

    def run(self) -> None:
        """
            Run the worker
        """
        mp.current_process().name = '_WorldGen'
        w_seed = int.from_bytes(hashlib.sha256(str(self.seed).encode('utf-8')).digest(), 'little') // \
                 int.from_bytes(str(self.seed).encode('utf-8'), 'little')
        i = 0

        while not self.halted.is_set():
            request = self.requests.get()
            if self.halted.is_set():
                break
            i += 1
            cords = (request[0], request[1])
            if cords in self.generated:
                continue
            generated_tiles = self.generate(w_seed, cords)
            self.output.put((cords, generated_tiles))
            self.generated.append(cords)
            if not (i % 60):
                gc.collect()
        print('eie')

    def kill(self):
        self.halted.set()


class _WorldGenThread(_WorldGen, thr.Thread):
    """
        Thread version of WorldGen class
    """

    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)
        self.daemon = True
        self.name = '_WorldGenThread'


class _WorldGenProcess(_WorldGen, mp.Process):
    """
        Process version of WorldGen class
    """

    def __init__(self, room_options, seed, output):
        super().__init__(room_options=room_options, seed=seed, output=output)
        self.daemon = True
        self.name = '_WorldGenProcess'


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
        Base _WorldGenHandler class, distributes generation requests over workers' pool.
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
        self.workers_amount = 1
        self.distributor = SimpleDistributor(self.workers, _WorldGen.request)

    def request(self, x: int, y: int):
        """
            Request a room to be generated.

            :param x: Room's X coordinate
            :param y: Room's Y coordinate
        """
        self.requests.put((x, y))

    def halt(self):
        """
            Send a message to all workers to stop the generation process.
        """
        self.requests.put(None)

    def run(self) -> None:
        """
            Run the handler
        """
        mp.current_process().name = "WorldGenHandler"
        self.workers = [self.worker(self.room_options, self.seed, self.output)
                        for _ in range(self.workers_amount)]
        self.distributor = SimpleDistributor(self.workers, _WorldGen.request)
        [worker.start() for worker in self.workers]
        [self.distributor(*request) for request in iter(self.requests.get, None)]
        [worker.kill() for worker in self.workers]
        [worker.join(timeout=2) for worker in self.workers]


class WorldGenHandlerProcess(_WorldGenHandler, mp.Process):
    """
        "Process controlling Threads" version of _WorldGenHandler
        Preferably use WorldGenHandler instead of this class.
    """

    def __init__(self, world_options):
        mp.Process.__init__(self)
        _WorldGenHandler.__init__(self, world_options)
        self.name = 'WorldGenHandlerProcess'
        self.worker = _WorldGenThread
        self.workers_amount = self.world_options.generator_threads


class WorldGenHandlerThread(_WorldGenHandler, thr.Thread):
    """
        "Thread controlling Processes" version of _WorldGenHandler
        Preferably use WorldGenHandler instead of this class.
    """

    def __init__(self, world_options):
        thr.Thread.__init__(self)
        _WorldGenHandler.__init__(self, world_options)
        self.name = 'WorldGenHandlerThread'
        self.workers_amount = self.world_options.generator_processes
