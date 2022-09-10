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

    def convert(self):
        self.surface = self.image.convert()


wall_types = {i: ImageSurface('NormalWall', i) for i in range(1, 7)}
floor = ImageSurface('NormalFloor')


def convert_images():
    [image_surface.convert() for image_surface in wall_types.values()]
    floor.convert()


class Room:
    def __init__(self):
        self.data = {'tiles': {}, 'entities': {}}
        self.entities = {}
        self.surface = pg.Surface(rs.room_size)
        self.drawn = False

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
                                         pg.Rect(cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1], *rs.tile_size))
                            blitRotateCenter(self.surface, wall_types[tile['type'][0]].surface,
                                             (cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1]),
                                             90 * (tile['type'][1] + 2))
                        case 'NormalFloor':
                            self.surface.blit(floor.surface, (cords[0] * rs.tile_size[0], cords[1] * rs.tile_size[1]))
                    self.data['tiles'][cords] = tile
        if 'entities' in data and data['entities'] != self.data['entities']:
            for entity in data['entities']:
                pg.draw.rect(self.surface, (255, 0, 0),
                             pg.Rect(entity.cords[0] * rs.tile_size[0], entity.cords[1] * rs.tile_size[1], 5, 5))
            self.data['entities'] = data['entities']
        return 0

    def visibility_set(self, b: bool):
        self.visible = b

    def draw(self, screen: pg.Surface, cords, camera):
        screen.blit(self.surface, (cords[0] - camera.position.x + 1000, cords[1] - camera.position.y + 1000))
        [entity.draw(screen) for entity in self.entities.values()]
