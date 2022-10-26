import multiprocessing as mp
import os

from logic.logistics import LogicProcess
from misc import ProjSettings
from time import sleep

class Manager:
    def __init__(self):
        self.render_queue: mp.Queue = mp.Queue(maxsize=1)
        self.entities_queue: mp.Queue = mp.Queue(maxsize=1)
        self.logic_queue: mp.Queue = mp.Queue(maxsize=100)
        self.halted: mp.Event = mp.Event()
        self.data = mp.Manager().Namespace()
        self.data.id_picked = 0
        self.data.data_picked = {}

    def get_camera_boundaries(self):
        if not self.render_queue.empty():
            return self.render_queue.get()
        return 0, 0, 0, 0

    def set_camera_boundaries(self, boundaries: tuple[int, int, int, int]):
        if self.render_queue.empty():
            self.render_queue.put(boundaries)

    def get_rooms(self):
        data = {}
        while not self.logic_queue.empty():
            data.update(self.logic_queue.get())
        return data

    def set_rooms(self, rooms):
        if self.logic_queue.empty():
            self.logic_queue.put(rooms)

    def set_entities(self, entities):
        if self.entities_queue.empty():
            self.entities_queue.put(entities)

    def get_entities(self):
        if not self.entities_queue.empty():
            data = self.entities_queue.get()
            return data
        return {}

if __name__ == '__main__':
    mp.current_process().name = "Antsy World"
    manager = Manager()

    logistics = LogicProcess(ProjSettings.SimSettings(), ProjSettings.WorldSettings(), manager)
    logistics.start()

    from ui.rendering import RenderThread
    sleep(3)
    rendering = RenderThread(manager)
    rendering.start()
    rendering.join()
    logistics.terminate()
    rendering.terminate()
