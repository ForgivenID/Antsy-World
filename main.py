import multiprocessing as mp

from logic.logistics import LogicProcess
from misc import ProjSettings
import pyglet as pyg
from pyglet.window import key


class Manager:
    def __init__(self):
        self.render_queue: mp.Queue = mp.Queue(maxsize=1)
        self.entities_queue: mp.Queue = mp.Queue(maxsize=1)
        self.logic_queue: mp.Queue = mp.Queue(maxsize=100)
        self.halted: mp.Event = mp.Event()

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

    from ui.rendering import EventProcess, DrawThread

    window = pyg.window.Window(*ProjSettings.RenderingSettings.window_size, "AntsyWorld", vsync=False, visible=False)
    rendering = DrawThread(window)
    events = EventProcess(manager)
    event_loop = pyg.app.EventLoop()
    pyg.clock.schedule_interval(rendering.update, 1/ProjSettings.RenderingSettings.framerate)
    pyg.clock.schedule_interval_soft(events.update, 2/ProjSettings.RenderingSettings.framerate)
    window.on_key_press = events.key_press
    window.on_key_release = events.key_release


    window.set_visible(True)
    pyg.app.run()

    logistics.join(1/100)
    logistics.terminate()
