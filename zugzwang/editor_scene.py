from __future__ import annotations

from typing import Dict, Any
import os
import chess
import pygame
import time

from zugzwang.group import Category
from zugzwang.scene import ZugScene, ZugSceneModel, ZugSceneView
from zugzwang.view import ZugView, ZugViewGroup, ZugTextView
from zugzwang.palette import DEFAULT_THEME as THEME
from zugzwang.graphics import PIECE_IMAGES, FLIP_IMAGE, TICK_IMAGE

# TODO: what up with this?
_SQ_SIZE = 60

class FenCreatorScene(ZugScene):
    def __init__(self, display, category: Category):
        model = FenCreatorModel()
        width = display.get_screen().get_width()
        height = display.get_screen().get_height()
        view = FenCreatorView(width, height)
        super().__init__(display, model, view)

        self._category = category

    def _left_click_registered(self, view_id: str):
        print("CLICKED:", view_id)
        if view_id == 'logo':
            self._display.pop_scene()
            return

        if view_id.startswith('board'):
            _, symbol = tuple(view_id.split('.'))
            square = chess.parse_square(symbol)
            if self._model.piece == self._model.get_piece_at(square):
                
                self._model.set_piece_at(square, None)
            else:
                self._model.set_piece_at(square, self._model.piece)

        elif view_id.startswith('piece'):
            _, symbol = tuple(view_id.split('.'))
            piece = chess.Piece.from_symbol(symbol)
            new_piece = None if self._model.piece == piece else piece
            self._model.set_piece(new_piece)

        elif view_id == 'turn':
            self._model.toggle_turn()
            self.refresh()

        elif view_id == 'flip':
            self._model.toggle_perspective()
            self.refresh()

        elif view_id == 'clear':
            for square in chess.SQUARES:
                self._model.set_piece_at(square, None)
            self.refresh()
        
        elif view_id == 'tick':
            self._display.pop_scene()
            

    def _chess_square(self, row: int, column: int):
        if self._model.perspective == chess.WHITE:
            return ((7 - row) * 8) + column
        else:
            return (row * 8) + (7 - column)
            
    def _right_click_registered(self, element):

        if not self._model.is_valid():
            return

        if element.view_id.startswith('board'):
            _, name = tuple(element.view_id.split('.'))
            square = chess.parse_square(name)
            
            if square in self._model.ROOK_SQUARES:
                self._model.toggle_castling(square)
                    
            elif square in self._model.EP_SQUARES:
                old_ep = self._model.ep
                self._model.ep = square
                if not self._model.is_valid():
                    self._model.ep = old_ep


    def update(self):

        # the model may be invalid - in which case, set castling and en passent defaults
        if not self._model.is_valid():
            self._model.flatten_castling()
            self._model.set_ep(None)

        # board pieces
        for square in chess.SQUARES:
            piece = self._model.get_piece_at(square)
            square_name = chess.square_name(square)
            view_id = f'board.{square_name}'
            self._view.views[view_id].set_piece(piece)
        self._view.set_perspective(self._model.perspective)

        # board highlights
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            view_id = f'board.{square_name}'
            self._view.views[view_id].unhighlight()
        if self._model.is_valid():        
            highlights = []
            for square in (0, 7, 56, 63):
                if self._model.get_castling(square):
                    highlights.append(square)
            if self._model.ep:
                highlights.append(self._model.ep)
            for square in highlights:
                square_name = chess.square_name(square)
                view_id = f'board.{square_name}'
                self._view.views[view_id].highlight()

        # piece highlight
        for symbol in 'PNBRQKpnbrqk':
            view_id = f'piece.{symbol}'
            self._view.views[view_id].unhighlight()
        if self._model.piece:
            symbol = self._model.piece.symbol()
            view_id = f'piece.{symbol}'
            self._view.views[view_id].highlight()

        # turn
        self._view.views["turn"].set_turn(self._model.turn)

        # fen
        if self._model.is_valid():
            self._view.views["fen"].set_caption(self._model.fen())
            self._view.views["tick"].set_active()
        else:
            self._view.views["fen"].set_caption("")
            self._view.views["tick"].set_inactive()


class FenCreatorModel(ZugSceneModel):

    ROOK_SQUARES = (0, 7, 56, 63)
    
    _CASTLING = {
        0: 'Q',
        7: 'K',
        56: 'q',
        63: 'k',
    }

    EP_SQUARES = (
        24, 25, 26, 27, 28, 29, 30, 31,
        32, 33, 34, 35, 36, 37, 38, 39,
    )
    
    _EP = {
        24: 16,
        25: 17,
        26: 18,
        27: 19,
        28: 20,
        29: 21,
        30: 22,
        31: 23,
        32: 40,
        33: 41,
        34: 42,
        35: 43,
        36: 44,
        37: 45,
        38: 46,
        39: 47,
    }    
    
    def __init__(self):
        self._board = {square: None for square in chess.SQUARES}
        self.turn = chess.WHITE
        self.perspective = chess.WHITE
        self.piece = None
        self.ep = None
        self._castling = {
            7: False,   # 0-0
            0: False,   # 0-0-0
            63: False,  # ..0-0
            56: False,  # ..0-0-0
        }

    def get_piece_at(self, square: chess.Square):
        return self._board[square]
    
    def set_piece_at(self, square: chess.Square, piece: Optional[chess.Piece]):
        self._board[square] = piece
        
    def toggle_turn(self):
        self.turn = not self.turn

    def toggle_perspective(self):
        self.perspective = not self.perspective

    def set_piece(self, piece: Optional[chess.Piece]):
        self.piece = piece            
            
    def set_ep(self, square: Optional[chess.Square]):
        self.ep = square
            
    def toggle_castling(self, square: str):
        self._castling[square] = not self._castling[square]

    def get_castling(self, square: str):
        return self._castling[square]

    def set_castling(self, square: str, value: bool):
        self._castling[square] = value

    def flatten_castling(self):
        self._castling = {square: False for square in self._castling}

    def is_valid(self) -> bool:
        return chess.Board(self.fen()).is_valid()
            
    def fen(self) -> str:
        board = self._board_fen()
        turn = 'w' if self.turn == chess.WHITE else 'b'
        castling = self._castling_fen()
        ep = self._ep_fen()
        halfmove = '0'
        fullmove = '1'
        fen = ' '.join([board, turn, castling, ep, halfmove, fullmove])
        return fen

    def _board_fen(self):
        fen = ''
        for rank in range(8):
            for fle in range(8):
                piece = self._board[((7 - rank) * 8) + fle]
                symbol = piece.symbol() if piece is not None else " "
                fen = fen + symbol
            fen += '/'
        fen = fen[:-1]
        for i in range(8, 0, -1):
            fen = fen.replace((' ' * i), str(i))
        return fen

    def _ep_fen(self):
        return '-' if self.ep is None else chess.square_name(self._EP[self.ep])

    def _castling_fen(self):
        castling = ''.join(
            [self._CASTLING[c] for c in self._castling if self._castling[c]]
        )
        return castling if castling else '-'

class FenCreatorView(ZugSceneView):

    _LABELS = [
        'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1',
        'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8'
    ]

    def __init__(self, width: int, height: int):
        super().__init__(width, height)        

        # board
        #l = 180
        #t = 80
        #self.board = {}
        #for square in chess.SQUARES:
        #    colour = chess.WHITE if ((square // 8) + square) % 2 == 0 else chess.BLACK
        #    square_name = chess.square_name(square)
        #    view_id = f"board.{square_name}"
        #    position = pygame.Rect(0, 0, 0, 0)
        #    label = square_name if square_name in self._LABELS else None
        #    self._add_item(view_id, ZugSquareView(view_id, rect, colour, label=label)
        #self.set_perspective(chess.WHITE)

        # piece selector
        #l = 720
        #t = 260
        #self.selector = {}
        #for row, piece_colour in enumerate((chess.WHITE, chess.BLACK)):
        #    for column, piece_type in enumerate(
        #        (chess.PAWN, chess.KNIGHT, chess.BISHOP,
        #         chess.ROOK, chess.QUEEN, chess.KING)
        #    ):
        #        x = l + (column * _SQ_SIZE)
        #        y = t + (row * _SQ_SIZE)
        #        rect = pygame.Rect(x, y, _SQ_SIZE, _SQ_SIZE)
        #        colour = chess.WHITE if (row + column) % 2 == 0 else chess.BLACK
        #        piece = chess.Piece(piece_type, piece_colour)
        #        view_id = f"piece.{piece.symbol()}"
        #        self.views[view_id] = (ZugSquareView(view_id, rect, colour, piece))

        # thumbs
        x = 60
        y = 80
        position = (x, y)
        self._add_item("turn", position, TurnView())
        position = (x, y + _SQ_SIZE)
        self._add_item("flip", position, FlipView())
        position = (x, y + (2 * _SQ_SIZE))        
        self._add_item("clear", position, ClearView())

        # fen
        x = 180
        y = 640
        position = (x, y)
        self._add_item("fen", position, FenView(THEME.black, THEME.white))
        position = (x + (7 * _SQ_SIZE), y)
        self._add_item("tick", position, TickView())

    def set_perspective(self, colour: chess.Colour):
        for square in chess.SQUARES:
            view_id = f"board.{chess.square_name(square)}"
            rect = self._coordinates(square, colour)
            print(square, view_id, rect)
            self.views[view_id].rect = rect

    def _coordinates(self, square: chess.Square, perspective: chess.Colour):
        if perspective == chess.WHITE:
            return pygame.Rect(
                self._board_x + (chess.square_file(square) * _SQ_SIZE),
                self._board_y + ((7 - chess.square_rank(square)) * _SQ_SIZE),
                _SQ_SIZE,
                _SQ_SIZE,
            )
        else:
            return pygame.Rect(
                self._board_x + (7 - chess.square_file(square)) * _SQ_SIZE,
                self._board_y + (chess.square_rank(square) * _SQ_SIZE),
                _SQ_SIZE,
                _SQ_SIZE,                
            )
    

class ZugSquareView:
    def __init__(
            self,
            view_id: str,
            rect: pygame.Rect,
            colour: chess.Color,
            piece: Optional[chess.Piece]=None,
            label: Optional[str]=None
    ):
        self.view_id = view_id
        self.rect = rect
        self._colour = colour
        self._piece = piece
        self._label = label
        self._highlighted = False
        self._font = pygame.font.SysFont(None, 20)        

    def set_highlight(self, highlighted: bool):
        self._highlighted = higlighted

    def highlight(self):
        self._highlighted = True

    def unhighlight(self):
        self._highlighted = False

    def set_piece(self, piece: Optional[chess.Piece]):
        self._piece = piece

    def draw(self, screen: pygame.Surface):
        colour = self._background_colour()        
        pygame.draw.rect(screen, colour, self.rect)
        if self._label is not None and not self._highlighted:
            label = self._font.render(self._label, True, self._label_colour())
            label_rect = label.get_rect()
            label_rect.right = self.rect.x + 58
            label_rect.top = self.rect.y + 2
            screen.blit(label, (label_rect))
        if self._piece is not None:
            screen.blit(PIECE_IMAGES.get(self._piece), (self.rect.x, self.rect.y))
            
    def _background_colour(self):
        if self._highlighted:
            return THEME.white_highlight if self._colour == chess.WHITE \
                else THEME.black_highlight
        else:
            return THEME.white if self._colour == chess.WHITE else THEME.black

    def _label_colour(self):
        return THEME.black if self._colour == chess.WHITE else THEME.white
        

class TurnView(ZugView):

    _WIDTH = _SQ_SIZE
    _HEIGHT = _SQ_SIZE
    
    def __init__(self):
        super().__init__()
        self._turn = chess.WHITE
    
    def set_turn(self, turn: chess.Color):
        self._turn = turn

    def draw(self) -> pygame.Surface:
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))
        surface.fill(THEME.white)
        piece = chess.Piece(chess.KING, self._turn)
        surface.blit(PIECE_IMAGES.get(piece), (0,0))
        return surface


class FlipView(ZugView):

    _WIDTH = _SQ_SIZE
    _HEIGHT = _SQ_SIZE    
    
    def draw(self) -> pygame.Surface:
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))
        surface.fill(THEME.black)
        surface.blit(FLIP_IMAGE, 4, 4))
        return surface


class ClearView(ZugView):

    _WIDTH = _SQ_SIZE
    _HEIGHT = _SQ_SIZE    
    
    def draw(self) -> pygame.Surface:
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))        
        for i in range(8):
            for j in range(8):
                colour = THEME.white if (i + j) % 2 == 0 else THEME.black
                x = (i * _SQ_SIZE) // 8
                y = (j * _SQ_SIZE) // 8
                x1 = ((i + 1) * _SQ_SIZE) // 8
                y1 = ((j + 1) * _SQ_SIZE) // 8
                rect = pygame.Rect(x, y, x1 - x, y1 - y)
                pygame.draw.rect(surface, colour, rect)
        return surface


class FenView(ZugTextView):

    _WIDTH = 7 * _SQ_SIZE
    _HEIGHT = _SQ_SIZE


class TickView(ZugView):

    _WIDTH = _SQ_SIZE
    _HEIGHT = _SQ_SIZE    

    def __init__(self):
        super().__init__()
        self._active = False
    
    def set_active(self):
        self._active = True
        
    def set_inactive(self):
        self._active = False
        
    def draw(self):
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))
        surface.fill(THEME.black)
        if self._active is True:
            surface.blit(TICK_IMAGE, (0,0))
        return surface
