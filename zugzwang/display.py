from __future__ import annotations

import pygame
import chess
import random
import os
from typing import Dict, List, Any

pygame.init()


class ZugDisplay:
    def __init__(self):
        self._scenes = []
        self._scene = None
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        self._screen = pygame.display.set_mode([width, height], pygame.FULLSCREEN)

    def get_rect(self):
        return self._screen.get_rect()

    def get_screen(self):
        return self._screen

    def push_scene(self, scene: ZugScene):
        scene.refresh()
        self._scenes.append(scene)
        self._set_scene(scene)

    def _set_scene(self, scene: ZugScene):
        self._scene = scene

    def pop_scene(self):
        self._scenes.pop()
        if self._scenes:
            scene = self._scenes[-1]
            scene.refresh()
            self._set_scene(scene)
        else:
            pygame.QUIT

    def main(self):
        clock = pygame.time.Clock()
        running = True
        while running:

            # delegate event handling to the scene
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                self._scene.handle_event(event)

            # limit redraw rate to 30 fps
            clock.tick(30)
            pygame.display.flip()
