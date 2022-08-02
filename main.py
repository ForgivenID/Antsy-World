import multiprocessing as mp

from misc import ProjSettings
from world import World


class LogicProcess(mp.Process):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    from ui.rendering import RenderThread
    world = World(ProjSettings.SimSettings(), ProjSettings.WorldSettings())
    rendering = RenderThread(world)
    rendering.start()
    rendering.join()
    world.save()
    world.quit()
    pass