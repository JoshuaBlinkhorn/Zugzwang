from __future__ import annotations

import pygame
import chess
import random
import os
from typing import Dict, List, Any

from zugzwang.group import ZugUserData
from zugzwang.palette import THEME as THEME

pygame.init()

_SQ_SIZE = 60


class ColourScheme:
    def __init__(
        self,
        white,
        black,
        white_highlight,
        black_highlight,
        white_move_highlight,
        black_move_highlight,
    ):
        self.white = white
        self.black = black
        self.white_highlight = white_highlight
        self.black_highlight = black_highlight
        self.white_move_highlight = white_move_highlight
        self.black_move_highlight = black_move_highlight


THEME = ColourScheme(
    white=(237, 220, 180),
    black=(180, 134, 100),
    white_highlight=(113, 143, 101),
    black_highlight=(99, 117, 81),
    white_move_highlight=(190, 198, 100),
    black_move_highlight=(158, 156, 40),
)

_PIECE_IMAGES = {
    chess.Piece(chess.PAWN, chess.WHITE): pygame.image.load("img/white_pawn.png"),
    chess.Piece(chess.KNIGHT, chess.WHITE): pygame.image.load("img/white_knight.png"),
    chess.Piece(chess.BISHOP, chess.WHITE): pygame.image.load("img/white_bishop.png"),
    chess.Piece(chess.ROOK, chess.WHITE): pygame.image.load("img/white_rook.png"),
    chess.Piece(chess.QUEEN, chess.WHITE): pygame.image.load("img/white_queen.png"),
    chess.Piece(chess.KING, chess.WHITE): pygame.image.load("img/white_king.png"),
    chess.Piece(chess.PAWN, chess.BLACK): pygame.image.load("img/black_pawn.png"),
    chess.Piece(chess.KNIGHT, chess.BLACK): pygame.image.load("img/black_knight.png"),
    chess.Piece(chess.BISHOP, chess.BLACK): pygame.image.load("img/black_bishop.png"),
    chess.Piece(chess.ROOK, chess.BLACK): pygame.image.load("img/black_rook.png"),
    chess.Piece(chess.QUEEN, chess.BLACK): pygame.image.load("img/black_queen.png"),
    chess.Piece(chess.KING, chess.BLACK): pygame.image.load("img/black_king.png"),
}

_FLIP_IMAGE = pygame.transform.scale(pygame.image.load("img/flip.png"), (50, 50))
_TICK_IMAGE = pygame.transform.scale(pygame.image.load("img/tick.png"), (50, 50))


def create_logo() -> pygame.Surface:
    font = pygame.font.SysFont(None, 90)
    Zugzw = font.render("ZUGZW", True, (255, 255, 255))
    ng = font.render("NG", True, (255, 255, 255))
    piece = _PIECE_IMAGES[chess.Piece.from_symbol("N")]

    logo = pygame.Surface((380, 80))
    logo.blit(Zugzw, (0, 0))
    logo.blit(piece, (215, -2))
    logo.blit(ng, (270, 0))

    return logo


_LOGO = create_logo()


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
                    self._down = None
                    if event.button == 1:
                        self._click_registered(element)
                        break
                    if event.button == 3:
                        self._right_click_registered(element)
                        break

    def update(self):
        pass

    def draw(self):
        for element in self._elements:
            element.draw(self._screen)

    def _click_registered(self, element):
        element.clicked()


class ZugDisplay:
    def __init__(self):
        self._scenes = []
        self._scene = None
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        self._screen = pygame.display.set_mode([width, height], pygame.FULLSCREEN)

    def get_rect(self):
        return self._screen.get_rect()

    def push_scene(self, scene: ZugScene):
        self._scenes.append(scene)
        self._set_scene(scene)

    def _set_scene(self, scene: ZugScene):
        self._scene = scene

    def pop_scene(self):
        self._scenes.pop()
        if self._scenes:
            self._set_scene(self._scenes[-1])
        else:
            pygame.QUIT

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
                self._scene.draw(self._screen)

            clock.tick(30)
            pygame.display.flip()


class ZugFenCreatorModel:

    ROOK_SQUARES = (0, 7, 56, 63)

    _CASTLING = {
        0: "Q",
        7: "K",
        56: "q",
        63: "k",
    }

    EP_SQUARES = (
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
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
            7: False,  # 0-0
            0: False,  # 0-0-0
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
        turn = "w" if self.turn == chess.WHITE else "b"
        castling = self._castling_fen()
        ep = self._ep_fen()
        halfmove = "0"
        fullmove = "1"
        fen = " ".join([board, turn, castling, ep, halfmove, fullmove])
        return fen

    def _board_fen(self):
        fen = ""
        for rank in range(8):
            for fle in range(8):
                piece = self._board[((7 - rank) * 8) + fle]
                symbol = piece.symbol() if piece is not None else " "
                fen = fen + symbol
            fen += "/"
        fen = fen[:-1]
        for i in range(8, 0, -1):
            fen = fen.replace((" " * i), str(i))
        return fen

    def _ep_fen(self):
        return "-" if self.ep is None else chess.square_name(self._EP[self.ep])

    def _castling_fen(self):
        castling = "".join(
            [self._CASTLING[c] for c in self._castling if self._castling[c]]
        )
        return castling if castling else "-"


class ZugFenCreatorView:

    _LABELS = [
        "a1",
        "b1",
        "c1",
        "d1",
        "e1",
        "f1",
        "g1",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "h7",
        "h8",
    ]

    def __init__(self):

        self.views = {}
        self._board_x = 180
        self._board_y = 80

        # board
        l = 180
        t = 80
        self.board = {}
        for square in chess.SQUARES:
            colour = chess.WHITE if ((square // 8) + square) % 2 == 0 else chess.BLACK
            square_name = chess.square_name(square)
            view_id = f"board.{square_name}"
            rect = pygame.Rect(0, 0, 0, 0)
            label = square_name if square_name in self._LABELS else None
            self.views[view_id] = ZugSquareView(view_id, rect, colour, label=label)
        self.set_perspective(chess.WHITE)

        # piece selector
        l = 720
        t = 260
        self.selector = {}
        for row, piece_colour in enumerate((chess.WHITE, chess.BLACK)):
            for column, piece_type in enumerate(
                (
                    chess.PAWN,
                    chess.KNIGHT,
                    chess.BISHOP,
                    chess.ROOK,
                    chess.QUEEN,
                    chess.KING,
                )
            ):
                x = l + (column * _SQ_SIZE)
                y = t + (row * _SQ_SIZE)
                rect = pygame.Rect(x, y, _SQ_SIZE, _SQ_SIZE)
                colour = chess.WHITE if (row + column) % 2 == 0 else chess.BLACK
                piece = chess.Piece(piece_type, piece_colour)
                view_id = f"piece.{piece.symbol()}"
                self.views[view_id] = ZugSquareView(view_id, rect, colour, piece)

        # thumbs
        l = 60
        t = 80
        rect = pygame.Rect(l, t, _SQ_SIZE, _SQ_SIZE)
        self.views["turn"] = ZugTurnView("turn", rect)
        rect = pygame.Rect(l, t + (_SQ_SIZE), _SQ_SIZE, _SQ_SIZE)
        self.views["flip"] = ZugFlipView("flip", rect)
        rect = pygame.Rect(l, t + (2 * _SQ_SIZE), _SQ_SIZE, _SQ_SIZE)
        self.views["clear"] = ZugClearView("clear", rect)

        # fen
        l = 180
        t = 640
        rect = pygame.Rect(l, t, _SQ_SIZE * 7, _SQ_SIZE)
        self.views["fen"] = ZugTextView("fen", rect)
        rect = pygame.Rect(l + (7 * _SQ_SIZE), t, _SQ_SIZE, _SQ_SIZE)
        self.views["tick"] = ZugTickView("tick", rect)

    def set_perspective(self, colour: chess.Colour):
        for square in chess.SQUARES:
            vid = f"board.{chess.square_name(square)}"
            rect = self._coordinates(square, colour)
            print(square, vid, rect)
            self.views[vid].rect = rect

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
        piece: Optional[chess.Piece] = None,
        label: Optional[str] = None,
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
            screen.blit(_PIECE_IMAGES.get(self._piece), (self.rect.x, self.rect.y))

    def _background_colour(self):
        if self._highlighted:
            return (
                THEME.white_highlight
                if self._colour == chess.WHITE
                else THEME.black_highlight
            )
        else:
            return THEME.white if self._colour == chess.WHITE else THEME.black

    def _label_colour(self):
        return THEME.black if self._colour == chess.WHITE else THEME.white


class ZugTurnView:
    def __init__(self, view_id: str, rect: pygame.Rect):
        self.view_id = view_id
        self.rect = rect
        self._turn = chess.WHITE

    def set_turn(self, turn: chess.Color):
        self._turn = turn

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, THEME.white, self.rect)
        piece = chess.Piece(chess.KING, self._turn)
        screen.blit(_PIECE_IMAGES.get(piece), (self.rect.x, self.rect.y))


class ZugFlipView:
    def __init__(self, view_id: str, rect: pygame.Rect):
        self.view_id = view_id
        self.rect = rect

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, THEME.black, self.rect)
        screen.blit(_FLIP_IMAGE, (self.rect.x + 5, self.rect.y + 5))


class ZugClearView:
    def __init__(self, view_id: str, rect: pygame.Rect):
        self.view_id = view_id
        self.rect = rect

    def draw(self, screen: pygame.Surface):
        for i in range(8):
            for j in range(8):
                colour = THEME.white if (i + j) % 2 == 0 else THEME.black
                x = self.rect.x + (i * _SQ_SIZE) // 8
                y = self.rect.y + (j * _SQ_SIZE) // 8
                x1 = self.rect.x + ((i + 1) * _SQ_SIZE) // 8
                y1 = self.rect.y + ((j + 1) * _SQ_SIZE) // 8
                rect = pygame.Rect(x, y, x1 - x, y1 - y)
                pygame.draw.rect(screen, colour, rect)


class ZugTextView:
    def __init__(self, view_id: str, rect: pygame.Rect, caption: str = None):
        self.view_id = view_id
        self.rect = rect
        self._caption = caption
        self._font = pygame.font.SysFont(None, 24)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, THEME.white, self.rect)
        if self._caption:
            image = self._font.render(self._caption, True, (0, 0, 0))
            screen.blit(image, (self.rect.x + 5, self.rect.y + 5))

    def set_caption(self, caption):
        self._caption = caption


class ZugTickView:
    def __init__(self, view_id: str, rect: pygame.Rect):
        self.view_id = view_id
        self.rect = rect
        self._active = False

    def set_active(self):
        self._active = True

    def set_inactive(self):
        self._active = False

    def draw(self, screen: pygame.Surface):
        colour = THEME.black
        pygame.draw.rect(screen, colour, self.rect)
        if self._active is True:
            screen.blit(_TICK_IMAGE, (self.rect.x + 5, self.rect.y + 5))


class ZugFenCreator:
    def __init__(self, display: ZugDisplay):
        self._display = display
        self._model = ZugFenCreatorModel()
        self._view = ZugFenCreatorView()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for view in self._view.views.values():
                if view.rect.collidepoint(event.pos):
                    self._down = view
                    break
        if event.type == pygame.MOUSEBUTTONUP:
            for view in self._view.views.values():
                if view.rect.collidepoint(event.pos) and self._down == view:
                    self._down = None
                    if event.button == 1:
                        self._left_click_registered(view)
                        break
                    if event.button == 3:
                        self._right_click_registered(view)
                        break

    def _left_click_registered(self, view):

        vid = view.view_id

        if vid.startswith("board"):
            _, symbol = tuple(vid.split("."))
            square = chess.parse_square(symbol)
            if self._model.piece == self._model.get_piece_at(square):

                self._model.set_piece_at(square, None)
            else:
                self._model.set_piece_at(square, self._model.piece)

        elif vid.startswith("piece"):
            _, symbol = tuple(vid.split("."))
            piece = chess.Piece.from_symbol(symbol)
            new_piece = None if self._model.piece == piece else piece
            self._model.set_piece(new_piece)

        elif vid == "turn":
            self._model.toggle_turn()

        elif vid == "flip":
            self._model.toggle_perspective()

        elif vid == "clear":
            for square in chess.SQUARES:
                self._model.set_piece_at(square, None)

        elif vid == "tick":
            self._display.pop_scene()

    def _chess_square(self, row: int, column: int):
        if self._model.perspective == chess.WHITE:
            return ((7 - row) * 8) + column
        else:
            return (row * 8) + (7 - column)

    def _right_click_registered(self, element):

        if not self._model.is_valid():
            return

        if element.view_id.startswith("board"):
            _, name = tuple(element.view_id.split("."))
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
            view_id = f"board.{square_name}"
            self._view.views[view_id].set_piece(piece)
        self._view.set_perspective(self._model.perspective)

        # board highlights
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            view_id = f"board.{square_name}"
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
                view_id = f"board.{square_name}"
                self._view.views[view_id].highlight()

        # piece highlight
        for symbol in "PNBRQKpnbrqk":
            view_id = f"piece.{symbol}"
            self._view.views[view_id].unhighlight()
        if self._model.piece:
            symbol = self._model.piece.symbol()
            view_id = f"piece.{symbol}"
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

    def draw(self):
        for view in self._view.views.values():
            view.draw(self._display.screen)
