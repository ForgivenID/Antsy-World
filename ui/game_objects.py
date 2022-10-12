from functools import cache
from pathlib import Path
from misc.ProjSettings import RenderingSettings as rs

import pyglet as pyg

from misc.Paths import cwd


@cache
def prepare_sprite(name, image_type=1):
    return pyg.image.load(Path(cwd, 'resources/sprites', name, name + str(image_type) + '.png'))


wall_types = {i: prepare_sprite('NormalWall', i) for i in range(1, 7)}
floor = prepare_sprite('NormalFloor')
ant = prepare_sprite('NormalAnt')


class Tile(pyg.sprite.Sprite):
    def __init__(self, img, room, cords, camera, *args, **kwargs):
        super(Tile, self).__init__(img, *args, **kwargs)
        self.camera = camera
        self.cords = cords
        self.room = room

    def transform(self):
        self.update(x=(self.cords[0]+self.room.cords[0]*rs.room_size[0]-round(self.camera.position[0], 3))*rs.tile_size[0], y=(self.cords[1]+self.room.cords[1]*rs.room_size[1]-round(self.camera.position[1], 3))*rs.tile_size[0], scale=1)


class Tileset:
    def __init__(self, batch):
        self.batch = batch

    def get_sprite(self, room, name, coordinates, camera, image_type, rotation):
        img = prepare_sprite(name, image_type)
        sprite = Tile(img, room, coordinates, camera, batch=self.batch, subpixel=True)
        sprite.update(rotation=(rotation+2) * -90)
        sprite.transform()
        return sprite


class Room:
    def __init__(self, cords, camera):
        self.data = {'tiles': {}, 'entities': {}}
        self.cords = cords
        self.entities = {}
        self.tile_batch = pyg.graphics.Batch()
        self.entity_batch = pyg.graphics.Batch()
        self.drawn = False
        self.entities_drawn = False
        self.tiles: dict[(int,int), pyg.sprite.Sprite] = {}
        self.tileset = Tileset(self.tile_batch)
        self.camera = camera

    def update(self, data) -> int:
        for tile in self.tiles.values():
            tile.transform()
        if 'tiles' in data and data['tiles'] != self.data['tiles']:
            self.drawn = False
            for cords, tile in data['tiles'].items():
                if cords not in self.data['tiles'] or self.data['tiles'][cords] != tile:
                    if cords in self.tiles:
                        self.tiles[cords].delete()
                    self.tiles[cords] = self.tileset.get_sprite(self, tile['object'], cords, self.camera, *tile['type'])
                    self.data['tiles'][cords] = tile
        if 'entities' in data and data['entities'] != self.data['entities']:
            self.entities_drawn = False
            # self.entity_surface.fill((0, 0, 0))
            for entity in data['entities'].values():
                '''self.entity_surface.set_colorkey((0, 0, 0))
                blitRotateCenter(self.entity_surface, ant.surface,
                                 (entity['cords'][0] * rs.tile_size[0], entity['cords'][1] * rs.tile_size[1]),
                                 (entity['rotation']))'''
                pass
            self.data['entities'] = data['entities']
        return 0

    def visibility_set(self, b: bool):
        self.visible = b

    def draw_tiles(self, cords, camera):
        # self.drawn = True
        self.tile_batch.draw()

    def draw_entities(self, cords, camera):
        # self.entities_drawn = True
        self.entity_batch.draw()
