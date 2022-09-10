import multiprocessing as mp
import random as rn

import misc.ProjSettings as settings
import worldgen
from logic.entities import BaseEntity, Ant
from world import World


class LogicProcess(mp.Process):
    def __init__(self, sim_settings, world_settings, manager):
        super(LogicProcess, self).__init__()
        self.world_settings = world_settings
        self.sim_settings = sim_settings
        self.tick = 0
        self.updates = mp.Queue()
        self.world = World(self.sim_settings, self.world_settings)
        self.entities: list[BaseEntity] = []
        self.requested = []
        self.manager = manager

    def run(self) -> None:
        self.generator = worldgen.WorldGenHandler(self.world_settings)
        self.generator.start()
        [self.get_rooms([(x, y)]) for x in range(10) for y in range(10)]
        for _ in range(100):
            data = self.generator.output.get()
            # print(data)
            data[1]['entities'] = []
            self.world.rooms_data[data[0]] = data[1]
        self.entities = [Ant((rn.randint(0, settings.RoomSettings.dimensions[0]),
                              rn.randint(0, settings.RoomSettings.dimensions[1])),
                             self.world.rooms_data[rn.choice(list(self.world.rooms_data.keys()))]) for _ in range(10)]
        while not self.manager.halted.is_set():
            self.update()
        self.generator.halt()
        self.generator.join(timeout=3)
        print('ended')

    def update(self):
        while not self.generator.output.empty():
            data = self.generator.output.get()
            # print(data)
            self.world.rooms_data[data[0]] = data[1]
        for entity in self.entities:
            entity.update(self.tick)
        tiled_area = self.manager.get_camera_boundaries()
        cords = [(x, y) for x in range(tiled_area[0], tiled_area[2]) for y in
                 range(tiled_area[1], tiled_area[3])]
        # print(tiles) if tiles != [] else None
        self.manager.set_rooms(self.get_rooms(cords))
        self.tick += 1

    def get_rooms(self, cords):
        output = {}
        for c in cords:
            if c in self.world.rooms_data:
                output[c] = self.world.rooms_data[c]
            elif c not in self.requested:
                self.requested.append(c)
                self.generator.request(*c)
                self.world.rooms_data[c] = {}
        return output
