import multiprocessing as mp
import threading as thr
import random as rn
from misc.Settings import SimSettings


class SmartDistributor:
    def __init__(self):
        raise NotImplemented


class SimpleDistributor:
    def __init__(self, objects, func):
        self.objects = objects
        self.func = func
        self.pointer = 0

    def __call__(self, *args, **kwargs):
        self.func(self.objects[self.pointer % len(self.objects)], *args, **kwargs)
        self.pointer += 1


class WorldGen:
    def __init__(self, room_options, rnd=rn.Random()):
        super().__init__()
        self.room_options = room_options
        self.random = rnd

    def generate(self, x, y):
        pass


class WorldGenThread(WorldGen, thr.Thread):
    def __init__(self, room_options, rnd=rn.Random()):
        super().__init__(room_options=room_options, rnd=rnd)


class WorldGenProcess(WorldGen, mp.Process):
    def __init__(self, room_options, rnd=rn.Random()):
        super().__init__(room_options=room_options, rnd=rnd)


class WorldGenHandler(mp.Process):
    def __init__(self, world_options, room_options):
        super(WorldGenHandler, self).__init__()

        self.requests = mp.Queue()
        self.output = mp.Queue()

        self.world_options = world_options
        self.room_options = room_options
        self.random = rn.Random(self.world_options.seed)

        self.worker = WorldGenThread
        if SimSettings.use_process_generation:
            self.worker = WorldGenProcess

        self.workers = [self.worker(self.room_options, self.random)
                        for _ in range(self.world_options.generator_processes)]

        self.distributor = SimpleDistributor(self.workers, WorldGen.generate)

    def run(self) -> None:
        for request in iter(self.requests.get, None):
            self.distributor(*request)
