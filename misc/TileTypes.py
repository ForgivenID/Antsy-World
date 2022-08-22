
class Tile:
    def __new__(cls, tile_type, rotation):
        return {'tile_type': tile_type, 'rotation': rotation}
