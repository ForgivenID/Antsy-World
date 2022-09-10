import math
import threading as thr
import uuid
from functools import lru_cache, cache

from logic.genome import Genome
from misc import ProjSettings


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


class Tile:
    def __init__(self):
        pass


class Room:
    def __init__(self, tiles):
        pass


class BaseEntity:
    def __init__(self, cords: tuple[int, int], room, rotation=0, name=None):
        self.room = room
        if name is None:
            name = f'{type(self)}_{uuid.uuid4()}'
        self.age = 0
        self.cords = cords
        self.rotation = rotation
        self.next_actions = []

    def update(self, tick):
        for action in self.next_actions:
            self.__dict__[action['type']](**action['args'])
        self.logic(tick)

    def logic(self, tick):
        self.age += 0.1


class Ant(BaseEntity):
    def __init__(self, cords: tuple[int, int], room, rotation=0):
        super(Ant, self).__init__(cords, room, rotation)
        self.sensory_types = ['age', 'my_energy', 'neighbour_count', 'room_population', 'fwd_view', 'obstacle_circle']
        self.reactivity_types = ['move_fwd', 'rotate-', 'rotate+']
        self.energy = 100
        self.room['entities'].append(self)
        self.genome = Genome(self)

    def get_sensory_val(self, sense):
        match sense:
            case 'age':
                return self.age
            case 'my_energy':
                return self.energy
            case 'room_population':
                return len(self.room['entities'])
            case 'fwd_view':
                x = int(self.cords[0] + math.cos(math.radians(self.rotation + 90)))
                y = int(self.cords[1] - math.sin(math.radians(self.rotation + 90)))
                return int(self.room['tiles'][(x, y)]['object'] == 'NormalWall' if (x, y) in self.room[
                    'tiles'] else 0)
            case 'obstacle_circle':
                return (sum([int(self.room['tiles'][(x + self.cords[0], y + self.cords[1])]['object'] == 'NormalWall'
                                 if (x + self.cords[0], y + self.cords[1]) in self.room['tiles'] else 0)
                             for x in range(-1, 2) for y in range(-1, 2)])) / 8
        return 0

    def perform(self, action):
        match action:
            case 'move_fwd':
                x = self.cords[0] + math.cos(math.radians(self.rotation))
                y = self.cords[1] - math.sin(math.radians(self.rotation))
                if (x + self.cords[0], y + self.cords[1]) in self.room['tiles']:
                    if self.room['tiles'][(x, y)]['object'] != 'NormalWall':
                        self.cords = (x, y)
            case 'rotate-':
                self.rotation -= 90
            case 'rotate+':
                self.rotation += 90

    def logic(self, tick):
        self.age += 0.1
        self.genome.brain.update_brain()
