from __future__ import annotations

import pygame

from zugzwang.display import ZugDisplay
from zugzwang.view import (
    ZugViewGroup,
    ZugLogoView,
)


class ZugScene:
    def __init__(
        self,
        display: ZugDisplay,
        model: ZugSceneModel,
        view: ZugSceneView,
    ):
        self._display = display
        self._model = model
        self._view = view

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._down = self._view.get_collision(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
            vid = self._view.get_collision(event.pos)
            if vid and self._down == vid:
                if event.button == 1:
                    self._left_click_registered(vid)
                if event.button == 3:
                    self._right_click_registered(vid)

    def _left_click_registered(self, view_id: str):
        print("left_click:", view_id)

    def _right_click_registered(self, view_id: str):
        print("right_click:", view_id)

    def _update(self):
        self._view.update(self._model)

    def _draw(self):
        self._display.get_screen().blit(self._view.draw(), (0, 0))

    def refresh(self):
        self._update()
        self._draw()


class ZugSceneModel:
    pass


class ZugSceneView(ZugViewGroup):

    # The scene's dimensions are that of the screen
    # They should be passed in by the scene's owner
    _WIDTH = None
    _HEIGHT = None

    def __init__(self, width: int, height: int):
        super().__init__()

        # dimensions
        self._width = width
        self._height = height

        # logo
        item_id = "logo"
        position = (10, 10)
        self._add_item(item_id, position, ZugLogoView())

    def get_width(self):
        return self._width

    def get_height(self):
        return self._width

    def update(self, model: ZugSceneModel):
        pass
