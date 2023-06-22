import pygame
from typing import List


class ZugSceneElement:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def clicked(self):
        print("I'm an element and you just clicked me.")


class ZugButton(ZugSceneElement):
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, (80, 80, 80), self.rect)


class ZugScene:
    def __init__(self, screen: pygame.Surface):
        self._screen = screen        
        self._down = None
        self._elements = []

    def add_element(self, element: ZugSceneElement):
        self._elements.append(element)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for element in self._elements:
                if element.rect.collidepoint(event.pos):
                    self._down = element
                    break
        if event.type == pygame.MOUSEBUTTONUP:
            for element in self._elements:
                if element.rect.collidepoint(event.pos) and element == self._down:
                    element.clicked()
                    self._down = None
                    break

    def update(self):
        pass

    def draw(self):
        for element in self._elements:
            element.draw(self._screen)


class ZugPositionSetupScene(ZugScene):
    def __init__(self, screen: pygame.Surface):
        self.__super__().init()

        
        self._elements.append(ZugButton(10, 10, 100, 100))


class ZugDisplay:

    def __init__(self):
        self._scenes = []
        self._scene = None
        self.screen = pygame.display.set_mode([480, 480])

    def add_scene(self, scene: ZugScene):
        self._scenes.append(scene)

    def set_scene(self, scene: ZugScene):
        self._scene = scene

    def main(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                self._scene.handle_event(event)
                self._scene.update()
                self._scene.draw()

            clock.tick(30)                
            pygame.display.flip()
    

if __name__ == '__main__':
    pygame.init()    
    display = ZugDisplay()
    setup_scene = ZugScene(display.screen)
    setup_scene.add_element(ZugButton(pygame.Rect(10, 10, 100, 100)))
    display.add_scene(setup_scene)
    display.set_scene(setup_scene)
    display.main()
