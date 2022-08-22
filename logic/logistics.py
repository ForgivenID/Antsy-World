import threading as thr
import multiprocessing as mp

import worldgen
from logic.entities import BaseEntity
from world import World


class LogicProcess(mp.Process):
    def __init__(self, sim_settings, world_settings):
        super(LogicProcess, self).__init__()
        self.world_settings = world_settings
        self.sim_settings = sim_settings
        self.tick = 0
        self.generator = worldgen.WorldGenHandler(self.world_settings)
        self.updates = mp.Queue()
        self.world = World(self.sim_settings, self.world_settings)
        self.entities: dict[tuple[int,int], BaseEntity] = {}

    def run(self) -> None:
        self.generator.run()

    def update(self):
        for entity in self.entities.values():
            entity.
        self.tick += 1

    def get_rooms(self, cords):
        output = {}
        for c in cords:
            if c in self.world.rooms_data:
                output[c] = self.world.rooms_data[c]
            else:
                self.generator.request(*c)
                self.world.rooms_data[c] = {}
        return output
