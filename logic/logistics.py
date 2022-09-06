import multiprocessing as mp

import worldgen
from logic.entities import BaseEntity
from world import World


class LogicProcess(mp.Process):
    def __init__(self, sim_settings, world_settings, manager):
        super(LogicProcess, self).__init__()
        self.world_settings = world_settings
        self.sim_settings = sim_settings
        self.tick = 0
        self.updates = mp.Queue()
        self.world = World(self.sim_settings, self.world_settings)
        self.entities: dict[tuple[int, int], BaseEntity] = {}
        self.requested = []
        self.manager = manager

    def run(self) -> None:
        self.generator = worldgen.WorldGenHandler(self.world_settings)
        self.generator.start()
        while not self.manager.halted.is_set():
            self.update()
        print('went wrong')
        self.generator.halt()

    def update(self):
        while not self.generator.output.empty():
            data = self.generator.output.get()
            # print(data)
            self.world.rooms_data[data[0]] = data[1]
        for entity in self.entities.values():
            pass
        tiled_area = self.manager.get_camera_boundaries()
        cords = [(x, y) for x in range(tiled_area[0], tiled_area[2]) for y in
                 range(tiled_area[1], tiled_area[3])]
        # print(tiles) if tiles != [] else None
        self.manager.set_rooms(self.get_rooms(cords))
        self.tick += 1

    def get_rooms(self, cords, f=True):
        output = {}
        for c in cords:
            if c in self.world.rooms_data:
                output[c] = self.world.rooms_data[c]
            elif c not in self.requested:
                self.requested.append(c)
                self.generator.request(*c)
                self.world.rooms_data[c] = {}
        return output
