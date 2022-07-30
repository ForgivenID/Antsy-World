import datetime
import uuid


class WorldSettings:
    dimensions: tuple[int, int] = (250, 250)
    generator_processes: int = 3
    generator_threads: int = 5
    portals: int = 2
    starting_colonies: int = 3
    name: str = str(uuid.uuid4())
    seed: str = str(uuid.uuid4())


# ---

class RoomSettings:
    dimensions: tuple[int, int] = (10, 10)
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
    dimensions: tuple[int, int] = (50, 50)
    name: str = str(uuid.uuid4())


class EmptyTile(TileSettings):
    interactable = False
    tickable = False
    walk_cost = 1


class SimSettings:
    worlds: int = 5
    portal_time: int = 10000
    use_process_generation: bool = True
    use_smart_request_distributor: bool = False
    name: str = datetime.datetime.now().strftime('%d.%m.%Y -- %H:%M:%S')
    room_settings = RoomSettings()
