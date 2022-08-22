import time
from functools import cached_property

from logic.logistics import Room
from misc import ProjSettings
import pickle as pkl
from pathlib import Path
from misc.Paths import cwd
import threading as thr

neighbors = lambda x, y, d: sum([int(d[x2, y2]) for x2 in range(x - 1, x + 2)
                                              for y2 in range(y - 1, y + 2)
                                              if (-1 < x < ProjSettings.WorldSettings.dimensions[0] and
                                                  -1 < y < ProjSettings.WorldSettings.dimensions[1] and
                                                  (x != x2 or y != y2) and
                                                  (0 <= x2 < ProjSettings.WorldSettings.dimensions[0]) and
                                                  (0 <= y2 < ProjSettings.WorldSettings.dimensions[1]))])


class WorldUpdater(thr.Thread):
    def __init__(self, world):
        super(WorldUpdater, self).__init__(daemon=True)
        self.killed = thr.Event()
        self.world = world

    def run(self) -> None:
        i = 0
        while not self.killed.is_set():
            i += 1
            self.world.et_updates()
            time.sleep(1/60)
            if i > 1000:
                i = 0

    def halt(self):
        self.killed.set()


class World:
    def __init__(self, sim_settings, world_settings):
        self.tick = 0
        self.rooms_data: dict[tuple[int, int], dict] = {}
        self.rooms = dict[tuple[int, int], Room]
        self.events = []
        self.sim_settings = sim_settings
        self.settings = world_settings
        self.updater = WorldUpdater(self)
        self.__create()


    def save(self) -> None:
        world_obj = {'tick': self.tick, 'rooms_data': self.rooms_data, 'settings': self.settings, 'events': self.events}
        Path(cwd, self.sim_settings.name, self.settings.name).mkdir(parents=True, exist_ok=True)

        with open(Path(cwd, self.sim_settings.name, self.settings.name, 'data.pk'), 'wb+') as savefile:
            pkl.dump(world_obj, savefile)

    def load(self) -> None:
        with open(Path(cwd, self.settings.name, 'data.pk'), 'rb') as savefile:
            world_obj = pkl.load(savefile)
            self.__dict__ |= world_obj


    def __create(self) -> None:
        print(self.settings.name, ':')
        print('; \n'.join([': '.join([str(tuple(map(str, cords))), repr(room)]) for cords, room in self.rooms_data.items()]))
        self.save()
        self.updater.start()
        self.save()

    def quit(self):
        self.save()


