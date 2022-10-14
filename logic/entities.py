import math
import random as rn
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
    def __init__(self, cords: tuple[int, int], room, world, rotation=0, name=None):
        self.room = room
        self.world = world
        if name is None:
            self.name = f'{type(self)}_{uuid.uuid4()}'
        self.age = 0
        self.cords = cords
        self.rotation = rotation
        self.next_actions = []
        self.alive = True

    def update(self, tick):
        self.logic(tick)

    def logic(self, tick):
        self.age += 0.1


class Ant(BaseEntity):

    def __init__(self, cords: tuple[int, int], room, world, queen, rotation=0):
        super(Ant, self).__init__(cords, room, world, rotation)
        self.sensory_types = ['age', 'my_energy', 'neighbour_count', 'room_population', 'fwd_view', 'obstacle_circle',
                              'sine', 'rotation']
        self.reactivity_types = ['move_fwd', 'rotate-', 'rotate+', 'pass', 'sine_coefficient', 'dig']
        self.energy = 100
        self.room['entities'][id(self)] = {'cords': self.cords, 'rotation': self.rotation, 'type': 'NormalAnt'}
        self.genome = Genome(self)
        self.rotation = rn.randint(0, 8) * 90
        self.queen: SwarmQueen = queen

    def move(self, x, y):
        if (x, y) in self.room['tiles']:
            if self.room['tiles'][(x, y)]['object'] != 'NormalWall':
                self.cords = (x, y)
        elif (0 > x or x > ProjSettings.RoomSettings.dimensions[0] - 1 or
              0 > y or y > ProjSettings.RoomSettings.dimensions[1] - 1):
            cords = (
                self.room['cords'][0] + (
                    (-1) if x < 0 else (1 if x > ProjSettings.RoomSettings.dimensions[0] - 1 else 0))
                ,
                self.room['cords'][1] + (
                    (-1) if y < 0 else (1 if y > ProjSettings.RoomSettings.dimensions[1] - 1 else 0)))
            new_room = self.world.rooms_data[cords] if cords in self.world.rooms_data else {}
            if 'entities' not in new_room:
                return
            self.room['entities'].pop(id(self))
            self.room = new_room
            self.cords = (x % ProjSettings.RoomSettings.dimensions[0], y % ProjSettings.RoomSettings.dimensions[1])
            self.room['entities'][id(self)] = {
                'cords': self.cords,
                'rotation': self.rotation
            }

    def rotate(self, angle):
        self.rotation += angle
        self.rotation %= 360

    def dig(self, x, y):
        if (x, y) in self.room['tiles']:
            if self.room['tiles'][(x, y)]['object'] == 'NormalWall':
                self.room['tiles'][(x, y)]['object'] = 'NormalFloor'
                self.world.reshape(self.room['cords'], (x,y))
        elif (0 > x or x > ProjSettings.RoomSettings.dimensions[0] - 1 or
              0 > y or y > ProjSettings.RoomSettings.dimensions[1] - 1):
            cords_ = (
                self.room['cords'][0] + (
                    (-1) if x < 0 else (1 if x > ProjSettings.RoomSettings.dimensions[0] - 1 else 0))
                ,
                self.room['cords'][1] + (
                    (-1) if y < 0 else (1 if y > ProjSettings.RoomSettings.dimensions[1] - 1 else 0)))
            new_room = self.world.rooms_data[cords_] if cords_ in self.world.rooms_data else {}
            if 'entities' not in new_room:
                return
            cords = (x % ProjSettings.RoomSettings.dimensions[0], y % ProjSettings.RoomSettings.dimensions[1])
            new_room['tiles'][cords]['object'] = 'NormalFloor'
            self.world.reshape(cords_, cords)

    def get_sensory_val(self, sense):
        match sense:
            case 'rotation':
                return self.rotation / 360
            case 'sine':
                return math.sin(self.age)
            case 'age':
                return self.age
            case 'my_energy':
                return self.energy / 100
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
        match action[0]:
            case 'move_fwd':
                x = int(round(self.cords[0] + math.cos(math.radians(self.rotation))))
                y = int(round(self.cords[1] - math.sin(math.radians(self.rotation))))
                self.next_actions.append(('move', (x, y)))

            case 'rotate-':
                self.next_actions.append(('rotate', tuple([-90])))
            case 'rotate+':
                self.next_actions.append(('rotate', tuple([+90])))
            case 'dig':
                x = int(round(self.cords[0] + math.cos(math.radians(self.rotation))))
                y = int(round(self.cords[1] - math.sin(math.radians(self.rotation))))
                self.next_actions.append(('dig', (x, y)))
            case _:
                self.energy -= 0.0001

    def apply(self):
        if self.energy < 0:
            if id(self) in self.room['entities']:
                self.room['entities'].pop(id(self))
            self.alive = False
            del self
        else:
            self.age += 0.1
            [Ant.__dict__[action](self, *args) for action, args in self.next_actions]
            self.next_actions.clear()
            self.energy -= 0.01
            self.room['entities'][id(self)]['cords'] = self.cords
            self.room['entities'][id(self)]['rotation'] = self.rotation

    def logic(self, tick):
        self.genome.brain.update_brain()

    def logic_async(self, tick):
        return self.genome.brain.update_brain_async()

    def update(self, tick):
        self.logic(tick)
        #
        # if self.queen.alive:
        #    return
        # else:
        #    self.logic(tick)


class SwarmQueen(BaseEntity):
    def __init__(self, cords, room, world, rotation=0):
        print(cords)
        super(SwarmQueen, self).__init__(cords, room, world, rotation)
        self.queen = None
        self.sensory_types = ['age', 'my_energy', 'neighbour_count', 'room_population', 'fwd_view', 'obstacle_circle',
                              'sine', 'ant_population']
        self.reactivity_types = ['create_ant', 'pass', 'sine_coefficient']
        self.energy = 10000
        self.room['entities'][id(self)] = {'cords': self.cords, 'rotation': self.rotation, 'type': 'SwarmQueen'}
        self.genome = Genome(self)
        self.rotation = rn.randint(0, 8) * 90
        self.ants: list[Ant] = []
        self.create_ant()

    def move(self, x, y):
        raise Warning(f'{self.name} has no ability to perform mobile actions, but desperately tries to.')

    def rotate(self, angle):
        raise Warning(f'{self.name} has no ability to perform mobile actions, but desperately tries to.')

    def get_sensory_val(self, sense):
        match sense:
            case 'sine':
                return math.sin(self.age)
            case 'age':
                return self.age
            case 'my_energy':
                return self.energy / 10000
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
        match action[0]:
            case 'create_ant':
                self.next_actions.append(('create_ant', ()))
            case _:
                self.energy -= 0.0001

    def create_ant(self):
        if self.energy > 10:
            self.energy -= 10
            ant = None
            for i in range(4):
                x = int(self.cords[0] + math.cos(math.radians(self.rotation + 90)))
                y = int(self.cords[1] - math.sin(math.radians(self.rotation + 90)))
                if self.room['tiles'][(x, y)]['object'] == 'NormalFloor' if (x, y) in self.room[
                    'tiles'] else False:
                    ant = Ant((x, y), self.room, self.world, self)
            if ant is None:
                if id(self) in self.room['entities']:
                    self.room['entities'].pop(id(self))
                self.alive = False
                del self
            else:
                self.ants.append(ant)

    def apply(self):
        if self.energy < 0:
            if id(self) in self.room['entities']:
                self.room['entities'].pop(id(self))
            self.alive = False
            del self
        else:
            self.age += 0.1
            [SwarmQueen.__dict__[action](self, *args) for action, args in self.next_actions]
            self.next_actions.clear()
            self.energy -= 0.01

    def logic(self, tick):
        self.age += 0.1
        self.genome.brain.update_brain()
        self.apply()
        [(ant.update(tick), ant.apply()) for ant in self.ants]
        # with Pool(processes=3) as p:
        #    data = p.starmap(Ant.logic_async, [(ant, tick) for ant in self.ants])
        # [(self.ants[i].perform(data[i]), self.ants[i].apply()) for i in range(len(data))]
