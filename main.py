import multiprocessing as mp
from pathlib import Path
import pickle as pk
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
    cmd = ''
    print('--ANTSY WORLD (RENDER/SIM SEPARATED) SIMULATION MANAGER--')
    print('[Use "help" if you are not familiar with this UI]\n')
    processes = {}
    while True:

        match cmd:
            case ['help' | 'h', *args]:
                match args:
                    case ['quit']:
                        print('quit -> exit all simulation and view windows, stop the program.')
                    case ['simulation' | 'sim', *args1]:
                        match args1:
                            case ['start']:
                                print('simulation start <sim_name> <TPS> -> start new simulation',
                                      'with name <sim_name> and tickspeed <TPS>', sep='\n')
                            case ['load']:
                                print('simulation load <sim_name> <TPS> -> continue simulation',
                                      'with name <sim_name> and tickspeed <TPS>', sep='\n')
                            case ['view']:
                                print('simulation view <sim_name> <TPS> <FPS> -> load and view simulation',
                                      'with name <sim_name> and tickspeed <TPS>,',
                                      'video will be shown with <FPS> framerate',
                                      sep='\n')
                            case []:
                                print('simulation <*args> -> start, continue or review simulations.',
                                      'possible <*args>: start, load, view.',
                                      'use - help simulation <*args> - to see more.', sep='\n')
                    case [] | ['help' | 'h']:
                        print('help <f_name> -> print info about a command.',
                              'possible <f_name>: help, simulation, quit.', sep='\n')
                    case _:
                        print(f'provided command "{" ".join(cmd)}" is not recognised as SimM functionality.')
                        print(f'proper usage of "{cmd[0]}":')
                        cmd = ['help', cmd[0]]
                        continue
            case ['simulation' | 'sim', *args]:
                match args:
                    case ['start', *args1]:
                        if len(args1) != 2:
                            print('unexpected arguments were provided.')
                            print(f'proper usage of "{cmd[0]} {cmd[1]}":')
                            cmd = ['help', 'simulation', 'start']
                            continue
                        sim_settings = ProjSettings.SimSettings()
                        sim_settings.name = cmd[2]
                        room_settings = ProjSettings.WorldSettings()
                        room_settings.name = cmd[2]
                        logistics = LogicProcess(sim_settings, room_settings, manager)
                        processes[cmd[2]] = logistics
                        logistics.start()
                    case ['load', *args1]:
                        if len(args1) != 2:
                            print('unexpected arguments were provided.')
                            print(f'proper usage of "{cmd[0]} {cmd[1]}":')
                            cmd = ['help', 'simulation', 'load']
                            continue
                        sim_settings = ProjSettings.SimSettings()
                        sim_settings.name = cmd[2]
                        room_settings = ProjSettings.WorldSettings()
                        room_settings.name = cmd[2]
                        logistics = LogicProcess(sim_settings, room_settings, manager)
                        try:
                            with open(Path('saves', cmd[2], cmd[2], 'data.pk'), 'rb') as save:
                                data = pk.load(save)
                                logistics.world = data['rooms_data'],
                                logistics.world_settings = data['settings']
                                logistics.tick = data['tick']
                        except Exception as exc:
                            print(f'while opening, an exception was raised:\n{exc}')

                        processes[cmd[2]] = logistics
                        logistics.start()
                    case _:
                        print(f'provided command "{" ".join(cmd)}" is not recognised as SimM functionality.')
                        print(f'proper usage of "{cmd[0]}":')
                        cmd = ['help', cmd[0]]
                        continue
            case ['quit']:
                for name, process in processes.items():
                    print(f'quitting process "{name}" -- {process}')
                    process.join(2)
                    process.terminate()
                exit(0)
        cmd = input('>> ').split()

    for name, process in processes.items():
        print('quitting', name)
        process.join(2)
        process.terminate()
