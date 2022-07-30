import pygame as pg
import game_objects as g_objects


class Camera:
    def __init__(self, renderer):
        self.camera_rect = pg.Rect(-100, 50, 100, -50)
        self.zoom = 1
        self.controllable = False
        self.renderer = renderer

    def update(self):
        pass


class Scene:
    def __init__(self, renderer):
        self.renderer = renderer
        self.screen = renderer.display
        self.objects: list[g_objects.BaseObject] = []
        self.ui: list[g_objects.BaseObject] = []
        self.sub = pg.surface.Surface(size=(10000, 10000))

    def update(self):
        self.objects.sort(key=lambda x: x.depth, reverse=False)
        self.ui.sort(key=lambda x: x.depth, reverse=False)

        # [obj.draw(self.sub) for obj in self.objects]
        pg.Rect(-5, 5, 5, -5)
        self.renderer.display.blit(self.sub.subsurface(self.renderer.camera.camera_rect))
        [obj.draw(self.renderer.display) for obj in self.ui]


class IntroScene(Scene):
    def __init__(self, renderer):
        super(IntroScene, self).__init__(renderer)
        self.objects.append()


class MainMenu(Scene):
    def __init__(self, renderer):
        super(MainMenu, self).__init__(renderer)


class RoomsView(Scene):
    def __init__(self, renderer):
        super(RoomsView, self).__init__(renderer)


class FarView(Scene):
    def __init__(self, renderer):
        super(FarView, self).__init__(renderer)


class EmptyScene(Scene):
    def __init__(self, renderer):
        super(EmptyScene, self).__init__(renderer)


class Renderer:
    def __init__(self, simulation):
        pg.init()
        pg.font.init()
        self.display = pg.display.set_mode((1200, 920))
        self.scenes = {
            'cuts': {
                'intro': IntroScene(self),
            },
            'menus': {
                'main_menu': MainMenu(self),
            },
            'game': {
                'lod_1': RoomsView(self),
                'lod_2': FarView(self),
            },
        }
        self.simulation = simulation
        self.current_scene = EmptyScene(self)
        self.camera = Camera(self)

    def update(self):
        self.current_scene.update()
