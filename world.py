from functools import cached_property
import random

from misc import Settings
import pickle as pkl
from pathlib import Path
from misc.Paths import cwd


class Tile:
    def __init__(self, cords):
        self.occupied = False
        self.settings = Settings.EmptyTile()
        self.cords = cords

    def move_from(self):
        self.occupied = False
        return True

    def move_to(self):
        if not self.occupied:
            self.occupied = True
            return True
        return False

    def update(self, tick, world, events=None):
        if self.settings.interactable:
            self.interaction_logic(tick, world, events)
        if self.settings.tickable:
            self.tick_logic(tick, world, events)

    def interaction_logic(self, tick, world, events=None):
        pass

    def tick_logic(self, tick, world, events=None):
        pass


class Material(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class Rock(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class Food(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class Nest(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class Room:
    def __init__(self, cords):
        self.layout = {}
        self.ants = {}
        self.tiles = {}
        self.settings = Settings.RoomSettings()
        self.cords = cords

    def update(self, tick, world, events=None):
        if events is None:
            events = []
        [tile.update(tick, world, events) for tile in self.tiles.values()]
        if len(self.ants) / self.settings.max_ants >= self.settings.ant_halt:
            if tick % 3 == 0:
                [ant.update() for ant in self.ants.values()]
        [ant.update() for ant in self.ants.values()]

    def generate(self):
        for x in range(self.settings.dimensions[0]):
            for y in range(self.settings.dimensions[1]):
                cords = (x, y)
                self.tiles[cords] = \
                    random.choices(population=[Material, Rock, Food], weights=self.settings.weights, k=1)[0](cords)

    @cached_property
    def translated(self):
        translated = {}
        for (x, y), tile in self.tiles:
            translated[((x+(self.settings.dimensions[0]*self.cords[0])),
                        (y+(self.settings.dimensions[1]*self.cords[1])))] = tile
        return translated

    def __repr__(self):
        return f'<{type(self).__name__} Room>'


class ColonialRoom(Room):
    def __init__(self, cords):
        super().__init__(cords)
        self.settings = Settings.ColonialRoomSettings()

class World:
    def __init__(self):
        self.tick = 0
        self.rooms: dict[tuple[int, int], Room] = {}
        self.events = []
        self.settings = Settings.WorldSettings()
        self.__create()

    def update(self):
        for k, v in self.rooms.items():
            v.update(self.tick, self, self.events)
        self.tick += 1

    def save(self):
        world_obj = {'tick': self.tick, 'rooms': self.rooms, 'settings': self.settings, 'events': self.events}
        Path(cwd, self.settings.name).mkdir(parents=True, exist_ok=True)
        with open(Path(cwd, self.settings.name, 'data.pk'), 'wb+') as savefile:
            pkl.dump(world_obj, savefile)

    def load(self):
        with open(Path(cwd, self.settings.name, 'data.pk'), 'rb') as savefile:
            world_obj = pkl.load(savefile)
            self.__dict__ = self.__dict__ | world_obj

    @cached_property
    def all_tiles(self):
        tiles = {}
        for room in self.rooms.values():
            tiles |= room.translated
        return tiles

    def __create(self):

        print(self.settings.name, ':')
        print('; \n'.join([': '.join([str(tuple(map(str, cords))), repr(room)]) for cords, room in self.rooms.items()]))
        self.save()
