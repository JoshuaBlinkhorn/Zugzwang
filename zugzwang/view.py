from __future__ import annotations

import pygame
import chess

from typing import Tuple, Union, Any

from zugzwang.graphics import PIECE_IMAGES

def create_logo() -> pygame.Surface:
    font = pygame.font.SysFont(None, 90)
    Zugzw = font.render("ZUGZW", True, (255, 255, 255))
    ng = font.render("NG", True, (255, 255, 255))
    piece = PIECE_IMAGES[chess.Piece.from_symbol('N')]

    logo = pygame.Surface((380, 80))
    logo.blit(Zugzw, (0, 0))
    logo.blit(piece, (215, -2))
    logo.blit(ng, (270, 0))

    return logo
    
_LOGO = create_logo()


class DuplicateIdError(ValueError):
    pass


class ZugView:

    _WIDTH = 100
    _HEIGHT = 100
    
    def __init__(self):
        pass

    @classmethod
    def get_width(cls):
        return cls._WIDTH

    @classmethod
    def get_height(cls):
        return cls._HEIGHT
        
    def update(self, model: Any):
        pass

    def draw(self) -> pygame.Surface:
        surface = pygame.Surface(self._WIDTH, self._HEIGHT)
        colour = (255, 255, 255)
        surface.fill(colour)
        return surface

    def get_collision(self, position: Tuple[int, int]):
        return True


class ZugLogoView(ZugView):
    _WIDTH = 380
    _HEIGHT = 80
    
    def draw(self):
        return _LOGO


class ZugTextView(ZugView):
    _WIDTH = 100
    _HEIGHT = 50
    
    def __init__(
            self,
            text_colour: Tuple[int, int, int] = (255, 255, 255),
            background_colour: Tuple[int, int, int] = (100, 100, 100),
            caption: str = None,
    ):
        super().__init__()
        self._text_colour = text_colour
        self._background_colour = background_colour
        self._caption = caption
        self._font = pygame.font.SysFont(None, 24)
    
    def draw(self) -> pygame.Surface:
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))
        surface.fill(self._background_colour)
        if self._caption:
            image = self._font.render(self._caption, True, self._text_colour)
            surface.blit(image, (5, 5))
        return surface

    def set_caption(self, caption):
        self._caption = caption


class ZugViewGroup:

    _WIDTH = 100
    _HEIGHT = 100
    
    def __init__(self):
        self._items = {}
        self._rects = {}

    def _add_item(
            self,
            item_id: str,
            position: Tuple[int, int],
            item: Union[ZugView, ZugViewGroup]
    ):
        if item_id in self._items:
            raise DuplicateIdError(item_id)
        rect = pygame.Rect(position[0], position[1], item.get_width(), item.get_height())
        self._rects[item_id] = rect
        self._items[item_id] = item

    @classmethod
    def get_width(cls):
        return cls._WIDTH

    @classmethod
    def get_height(cls):
        return cls._HEIGHT
        
    def draw(self) -> pygame.Surface:
        surface = pygame.Surface((self.get_width(), self.get_height()))
        for item_id, rect in self._rects.items():
            position = (rect.left, rect.top)
            surface.blit(self._items[item_id].draw(), position)
        return surface

    def get_collision(self, pos: Tuple[int, int]) -> Optional[str]:
        for item_id, rect in self._rects.items():
            if rect.collidepoint(pos):
                offset_pos = (pos[0] - rect.left, pos[1] - rect.top)
                collision = self._items[item_id].get_collision(offset_pos)
                if collision == True:
                    return item_id
                if collision != False:
                    return '.'.join([item_id, collision])
        return False
