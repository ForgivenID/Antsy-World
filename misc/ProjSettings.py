import datetime
import random as rn
import uuid

from win32api import GetSystemMetrics


class WorldSettings:
    dimensions: tuple[int, int] = (250, 250)
    generator_processes: int = 4
    generator_threads: int = 5
    portals: int = 2
    starting_colonies: int = 3
    name: str = str(uuid.uuid4())
    seed: str = str(rn.randint(1000, 9999))


# ---

class RoomSettings:
    dimensions: tuple[int, int] = (45, 45)
    name: str = str(uuid.uuid4())
    max_ants: int = 20
    ant_halt: float = .5
    weights = [1, 1, 1]


class NormalRoomSettings(RoomSettings):
    material_source_chance: float = 0.05
    rock_chance: float = .2
    food_chance: float = .1
    weights = [material_source_chance, rock_chance, food_chance]


class DesertRoomSettings(RoomSettings):
    material_source_chance: float = 0.15
    rock_chance: float = .005
    food_chance: float = .002
    weights = [material_source_chance, rock_chance, food_chance]


class ForestRoomSettings(RoomSettings):
    material_source_chance: float = 0.01
    rock_chance: float = .05
    food_chance: float = .15
    weights = [material_source_chance, rock_chance, food_chance]


class ColonialRoomSettings(RoomSettings):
    material_source_chance: float = 0.001
    rock_chance: float = 0
    food_chance: float = .2
    weights = [material_source_chance, rock_chance, food_chance]
    max_ants = 30


RngRoomTypes = [NormalRoomSettings, DesertRoomSettings, ForestRoomSettings]


# ---

class TileSettings:
    dimensions: tuple[int, int] = (30, 30)
    name: str = str(uuid.uuid4())


class EmptyTile(TileSettings):
    interactable = False
    tick_logic = False
    walk_cost = 1


class SimSettings:
    worlds: int = 5
    portal_time: int = 10000
    use_process_generation: bool = True
    use_smart_request_distributor: bool = False
    name: str = datetime.datetime.now().strftime('%d.%m.%Y %H-%M-%S')
    room_settings = RoomSettings()
    tickrate: float = 5.0  # ticks per second


class RenderingSettings:
    rendering_distance: int = 10
    framerate: int = 61
    fullscreen: bool = True
    window_size: tuple[int, int] = (1000, 1000)
    resolution: tuple[int, int] = (GetSystemMetrics(0), GetSystemMetrics(1))
    room_size: tuple[int, int] = (RoomSettings.dimensions[0] * TileSettings.dimensions[0],
                                  RoomSettings.dimensions[1] * TileSettings.dimensions[1])
    tile_size: tuple[int, int] = TileSettings.dimensions
    resizable: bool = True

class SwarmSettings:
    processes: int = 3


class GenomeSettings:
    module_restrictions: dict[str, tuple[int, int]] = {
        'movement': (0, 3),
        'rotation': (0, 2),
        'brain': (0, 1),
        'additional_cpu': (0, 3),
        'pickaxe': (0, 10),
        'sleepy_mode': (0, 15),
        'exploration': (0, 2),
    }
    max_brain_axons: int = 15
    starting_brain_axons: int = 6
    new_axon_mutation: float = 0.08
    axon_degeneration: float = 0.005
    function_mutation: float = 0.15
    weight_mutation: float = 0.1
