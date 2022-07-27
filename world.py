from functools import cached_property
import random

import worldgen
from misc import ProjSettings
import pickle as pkl
from pathlib import Path
from misc.Paths import cwd
from tiles import EmptyTile


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


class World:
    def __init__(self, sim_settings, world_settings):
        self.tick = 0
        self.rooms: dict[tuple[int, int], Room] = {}
        self.events = []
        self.sim_settings = sim_settings
        self.settings = world_settings
        self.generator = worldgen.WorldGenHandler(self.sim_settings.room_settings, self.settings)
        self.__create()

    def update(self) -> None:
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
            self.__dict__ = self.__dict__ | world_obj

    @cached_property
    def all_tiles(self):
        tiles = {}
        for room in self.rooms.values():
            tiles |= room.translated
        return tiles

    def __create(self) -> None:
        print(self.settings.name, ':')
        [room.generate() for room in self.rooms.values()]
        print('; \n'.join([': '.join([str(tuple(map(str, cords))), repr(room)]) for cords, room in self.rooms.items()]))
        self.save()
