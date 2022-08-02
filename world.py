import time
from functools import cached_property

import worldgen
from misc import ProjSettings
import pickle as pkl
from pathlib import Path
from misc.Paths import cwd
from tiles import EmptyTile
import threading as thr

neighbors = lambda x, y, d: sum([int(d[x2, y2]) for x2 in range(x - 1, x + 2)
                                              for y2 in range(y - 1, y + 2)
                                              if (-1 < x < ProjSettings.WorldSettings.dimensions[0] and
                                                  -1 < y < ProjSettings.WorldSettings.dimensions[1] and
                                                  (x != x2 or y != y2) and
                                                  (0 <= x2 < ProjSettings.WorldSettings.dimensions[0]) and
                                                  (0 <= y2 < ProjSettings.WorldSettings.dimensions[1]))])

class Room:
    def __init__(self, cords):
        self.layout = {}
        self.ants = {}
        self.tiles = {}
        self.settings = ProjSettings.RoomSettings()
        self.cords = cords

    def update(self, tick, world, events=None) -> None:
        if events is None:
            events = []
        [tile.update(tick, world, events) for tile in self.tiles.values()]
        if len(self.ants) / self.settings.max_ants >= self.settings.ant_halt:
            if tick % 3 == 0:
                [ant.update() for ant in self.ants.values()]
        [ant.update() for ant in self.ants.values()]

    def generate(self) -> None:
        for x in range(self.settings.dimensions[0]):
            for y in range(self.settings.dimensions[1]):
                cords = (x, y)
                self.tiles[cords] = EmptyTile(cords)

    @cached_property
    def translated(self):
        translated = {}
        for (x, y), tile in self.tiles:
            translated[((x + (self.settings.dimensions[0] * self.cords[0])),
                        (y + (self.settings.dimensions[1] * self.cords[1])))] = tile
        return translated

    def __repr__(self):
        return f'<{type(self).__name__} Room>'


class ColonialRoom(Room):
    def __init__(self, cords):
        super().__init__(cords)
        self.settings = ProjSettings.ColonialRoomSettings()


class WorldUpdater(thr.Thread):
    def __init__(self, world):
        super(WorldUpdater, self).__init__(daemon=True)
        self.killed = thr.Event()
        self.world = world

    def run(self) -> None:
        i = 0
        while not self.killed.is_set():
            i += 1
            self.world.get_generated()
            time.sleep(1/60)
            if not i % 120:
                self.world.update()
            if i > 1000:
                i = 0

    def halt(self):
        self.killed.set()


class World:
    def __init__(self, sim_settings, world_settings):
        self.tick = 0
        self.rooms: dict[tuple[int, int], dict] = {}
        self.events = []
        self.sim_settings = sim_settings
        self.settings = world_settings
        self.generator = worldgen.WorldGenHandler(self.settings)
        self.updater = WorldUpdater(self)
        self.__create()


    def update(self) -> None:
        print(self.rooms.keys())
        return
        for k, v in self.rooms.items():
            v.update(self.tick, self, self.events)
        self.tick += 1

    def save(self) -> None:
        world_obj = {'tick': self.tick, 'rooms': self.rooms, 'settings': self.settings, 'events': self.events}
        Path(cwd, self.sim_settings.name, self.settings.name).mkdir(parents=True, exist_ok=True)

        with open(Path(cwd, self.sim_settings.name, self.settings.name, 'data.pk'), 'wb+') as savefile:
            pkl.dump(world_obj, savefile)

    def load(self) -> None:
        with open(Path(cwd, self.settings.name, 'data.pk'), 'rb') as savefile:
            world_obj = pkl.load(savefile)
            self.__dict__ |= world_obj
        self.generator.halt()
        self.generator.join()
        del self.generator
        self.generator = worldgen.WorldGenHandler(self.settings)

    @cached_property
    def all_tiles(self):
        tiles = {}
        for room in self.rooms.values():
            tiles |= room.translated
        return tiles
    
    def get_generated(self):
        while not self.generator.output.empty():
            data = self.generator.output.get()
            self.rooms[data[0]] = data[1]
    
    def get_rooms(self, cords):
        output = {}
        for c in cords:
            if c in self.rooms:
                output[c] = self.rooms[c]
            else:
                self.generator.request(*c)
                self.rooms[c] = {}
        return output
        


    def __create(self) -> None:
        print(self.settings.name, ':')
        [room.generate() for room in self.rooms.values()]
        print('; \n'.join([': '.join([str(tuple(map(str, cords))), repr(room)]) for cords, room in self.rooms.items()]))
        self.save()
        self.generator.start()
        self.updater.start()
        self.save()

    def quit(self):
        self.generator.halt()
        self.generator.join()
        del self.generator
        self.save()


