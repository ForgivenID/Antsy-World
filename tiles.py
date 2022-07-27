from misc import ProjSettings


class Tile:
    def __init__(self, cords):
        self.occupied = False
        self.settings = ProjSettings.EmptyTile()
        self.cords = cords

    def move_from(self):
        self.occupied = False
        return True

    def move_to(self):
        if not self.occupied:
            self.occupied = True
            return True
        return False

    def update(self, tick, world, events=None) -> None:
        if self.settings.interactable:
            self.interaction_logic(tick, world, events)
        if self.settings.tickable:
            self.tick_logic(tick, world, events)

    def interaction_logic(self, tick, world, events=None):
        pass

    def tick_logic(self, tick, world, events=None):
        pass


class MaterialTile(Tile):
    def __init__(self, cords):
        super().__init__(cords)

    def move_to(self):
        return False


class RockTile(Tile):
    def __init__(self, cords):
        super().__init__(cords)

    def move_to(self):
        return False


class FoodTile(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class NestTile(Tile):
    def __init__(self, cords):
        super().__init__(cords)


class EmptyTile(Tile):
    def __init__(self, cords):
        super().__init__(cords)