import multiprocessing as mp

from logic.logistics import LogicProcess
from misc import ProjSettings


class Manager:
    def __init__(self):
        self.render_queue: mp.Queue = mp.Queue(maxsize=1)
        self.entities_queue: mp.Queue = mp.Queue(maxsize=1)
        self.logic_queue: mp.Queue = mp.Queue(maxsize=1)
        self.halted: mp.Event = mp.Event()

    def get_camera_boundaries(self):
        if not self.render_queue.empty():
            return self.render_queue.get()
        return 0, 0, 0, 0

    def set_camera_boundaries(self, boundaries: tuple[int, int, int, int]):
        if self.render_queue.empty():
            self.render_queue.put(boundaries)

    def get_rooms(self):
        if not self.logic_queue.empty():
            data = self.logic_queue.get()
            return data
        return {}

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

    rendering = RenderThread(manager)
    rendering.start()
    print(0)
    logistics.join()
    rendering.halt()
    rendering.terminate()
