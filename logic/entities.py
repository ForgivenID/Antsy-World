import threading as thr
import uuid

from logic.genome import Genome


class Tile:
    def __init__(self):
        pass


class Room:
    def __init__(self, tiles):
        pass


class BaseEntity(thr.Thread):
    def __init__(self, cords: tuple[int, int], rotation=0, name=None):
        if name is None:
            name = f'{type(self)}_{uuid.uuid4()}'
        super(BaseEntity, self).__init__(name=name)
        self.age = 0
        self.cords = cords
        self.rotation = rotation
        self.next_actions = []

    def update(self, tick):
        for action in self.next_actions:
            self.__dict__[action['type']](**action['args'])
        self.logic(tick)

    def logic(self, tick):
        self.age += 1


class Ant(BaseEntity):
    def __init__(self, cords: tuple[int, int], rotation=0):
        super(Ant, self).__init__(cords, rotation)
        self.genome = Genome()
