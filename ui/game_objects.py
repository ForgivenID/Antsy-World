from pathlib import Path

import pygame as pg

from misc.Paths import cwd
from misc.ProjSettings import RenderingSettings as rs


def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pg.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect)


class ImageSurface:
    def __init__(self, name='unspecified', image_type=1):
        # resources/sprites/NormalWall/NormalWall1.png
        self.surface = None
        self.image = pg.image.load(Path(cwd, 'resources/sprites', name, name + str(image_type) + '.png'))
        self.image = pg.transform.scale(self.image, (self.image.get_width() * 3, self.image.get_height() * 3))
        self.image.set_colorkey((0, 0, 0))

    def convert(self):
        self.image = self.image.convert()
        self.surface = self.image

class Tiles:
    wall_types = {i: ImageSurface('NormalWall', i) for i in range(1, 7)}
    floor = ImageSurface('NormalFloor')
    ant = ImageSurface('NormalAnt')


def convert_images():
    [image_surface.convert() for image_surface in Tiles.wall_types.values()]
    Tiles.floor.convert()
    Tiles.ant.convert()


class Room:
    def __init__(self):
        self.data = {'tiles': {}, 'entities': {}}
        self.entities = {}
        self.surface = pg.Surface(rs.room_size)
        self.entity_surface = pg.Surface((rs.room_size[0] + 10, rs.room_size[1] + 10))
        self.drawn = False
        self.entities_drawn = False

    def update(self, data) -> int:
        if 'tiles' in data and data['tiles'] != self.data['tiles']:
            self.drawn = False
            for cords, tile in data['tiles'].items():
                if cords not in self.data['tiles'] or self.data['tiles'][cords] != tile:
                    if self.surface.get_locked():
                        return 1
                    match tile['object']:
                        case 'NormalWall':
                            pg.draw.rect(self.surface, (0, 0, 0),
                                         pg.Rect(cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1],
                                                 *rs.tile_size))
                            blitRotateCenter(self.surface, Tiles.wall_types[tile['type'][0]].surface,
                                             (cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1]),
                                             90 * (tile['type'][1] + 2))
                        case 'NormalFloor':
                            self.surface.blit(Tiles.floor.surface,
                                              (cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1]))
                    self.data['tiles'][cords] = tile
        if 'entities' in data and data['entities'] != self.data['entities']:
            self.entities_drawn = False
            self.entity_surface.fill((0, 0, 0))
            for entity in data['entities'].values():
                blitRotateCenter(self.entity_surface, Tiles.ant.surface,
                                 (entity['cords'][0] * rs.tile_size[0] + 5, entity['cords'][1] * rs.tile_size[1] + 5),
                                 (entity['rotation']))
            self.data['entities'] = data['entities']
        return 0

    def visibility_set(self, b: bool):
        self.visible = b

    def draw_tiles(self, screen: pg.Surface, cords):
        self.drawn = True
        screen.blit(self.surface, (cords[0], cords[1]))

    def draw_entities(self, screen: pg.Surface, cords):
        self.entities_drawn = True
        '''pg.draw.rect(screen, (0, 0, 0),
                     pg.Rect(cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1],
                             *rs.room_size))'''
        screen.blit(self.entity_surface, (cords[0], cords[1]))

    def draw_data(self, screen: pg.Surface, _id):
        if _id or True:
            rect = pg.Rect(0,0, 100, 100)
            pg.draw.rect(screen, (0, 0, 0), rect)
