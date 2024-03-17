import pygame
import chess

from typing import List, Tuple, Dict, Callable


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


STANDARD_THEME = ColourScheme(
    white=(220, 220, 220),
    black=(180, 180, 180),
    white_highlight=(220, 220, 250),
    black_highlight=(180, 180, 230),
    white_move_highlight=(220, 250, 220),
    black_move_highlight=(180, 230, 180),
)

ROUGE_THEME = ColourScheme(
    white=(237, 220, 180),
    black=(180, 134, 100),
    white_highlight=(113, 143, 101),
    black_highlight=(99, 117, 81),
    white_move_highlight=(190, 198, 100),
    black_move_highlight=(158, 156, 40),
)


class ZugGUI:
    """Draws the chess board."""

    QUIT = "QUIT"

    _AWAITING_SOURCE = "AWAITING SOURCE"
    _AWAITING_TARGET = "AWAITING TARGET"
    _AWAITING_PROMOTION = "AWAITING PROMOTION"
    _SLEEPING = "SLEEPING"

    _SQUARE_SIZE = 60

    _PIECE_IMAGES = {
        chess.Piece(chess.PAWN, chess.WHITE): pygame.image.load("img/white_pawn.png"),
        chess.Piece(chess.KNIGHT, chess.WHITE): pygame.image.load(
            "img/white_knight.png"
        ),
        chess.Piece(chess.BISHOP, chess.WHITE): pygame.image.load(
            "img/white_bishop.png"
        ),
        chess.Piece(chess.ROOK, chess.WHITE): pygame.image.load("img/white_rook.png"),
        chess.Piece(chess.QUEEN, chess.WHITE): pygame.image.load("img/white_queen.png"),
        chess.Piece(chess.KING, chess.WHITE): pygame.image.load("img/white_king.png"),
        chess.Piece(chess.PAWN, chess.BLACK): pygame.image.load("img/black_pawn.png"),
        chess.Piece(chess.KNIGHT, chess.BLACK): pygame.image.load(
            "img/black_knight.png"
        ),
        chess.Piece(chess.BISHOP, chess.BLACK): pygame.image.load(
            "img/black_bishop.png"
        ),
        chess.Piece(chess.ROOK, chess.BLACK): pygame.image.load("img/black_rook.png"),
        chess.Piece(chess.QUEEN, chess.BLACK): pygame.image.load("img/black_queen.png"),
        chess.Piece(chess.KING, chess.BLACK): pygame.image.load("img/black_king.png"),
    }

    def __init__(self):
        pygame.init()
        self._screen = pygame.display.set_mode([480, 480])
        self._board = None
        self._move = None
        self._up = None
        self._down = None
        self._source = None
        self._target = None
        self._running = False
        self._status = self._AWAITING_SOURCE
        self._perspective = chess.WHITE
        self._colour_scheme = ROUGE_THEME

    def set_perspective(self, perspective: chess.Color):
        self._perspective = perspective

    def setup_position(self, board: chess.Board = None):
        self._board = board if board else chess.Board()
        self._draw_squares()
        self._highlight_move()
        self._draw_pieces()
        pygame.display.flip()

    def get_input(self):
        self._flush_events()
        self._status = self._AWAITING_SOURCE
        self._source = None
        self._target = None
        self._event_loop()
        return self._input

    def kill(self):
        pygame.quit()

    def _flush_events(self):
        for event in pygame.event.get():
            continue

    def _event_loop(self):
        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._input = self.QUIT
                    self._running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    self._mouse_down(pos)
                if event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    self._mouse_up(pos)
            pygame.display.flip()

    def _mouse_down(self, coordinates: Tuple[int, int]):
        square = self._get_square(coordinates)
        self._down = square

    def _mouse_up(self, coordinates: Tuple[int, int]):
        square = self._get_square(coordinates)
        if self._down == square:
            self._down = None
            self._clicked(square)

    def _clicked(self, square: chess.Square):
        if self._status == self._AWAITING_SOURCE:
            self._source_selected(square)
        elif self._status == self._AWAITING_TARGET:
            self._target_selected(square)
        elif self._status == self._AWAITING_PROMOTION:
            self._promotion_selected(square)

    def _reset(self):
        self._source = self._target = None
        self._status = self._AWAITING_SOURCE
        self.setup_position(self._board)

    def _source_selected(self, square: chess.Square):
        if not any(square == move.from_square for move in self._board.legal_moves):
            return
        self._source = square
        self._highlight_square(square)
        self._status = self._AWAITING_TARGET

    def _target_selected(self, square: chess.Square):
        self._target = square
        if self._source == self._target:
            self._reset()
            return
        if self._is_promotion():
            self._draw_promotion_choices()
            self._status = self._AWAITING_PROMOTION
        else:
            move = chess.Move(self._source, self._target)
            if move in self._board.legal_moves:
                self._move_registered(move)
            else:
                self._reset()
                self._target = None
                self._source_selected(square)

    def _promotion_selected(self, square: chess.Square):
        promotion_dict = self._promotion_dict()
        promotion = promotion_dict.get(square)
        if promotion == None:
            self._reset()
            return

        move = chess.Move(self._source, self._target, promotion)
        self._move_registered(move)

    def _move_registered(self, move):
        self._STATUS = self._SLEEPING
        self._input = move
        self._running = False

    def make_move(self, move):
        self._board.push(move)
        self._reset()
        self._STATUS = self._AWAITING_SOURCE

    def reset(self):
        self._reset()

    def _is_promotion(self) -> bool:
        """
        Check whether promotion to a queen is a legal move; and hence whether the move,
        as currently determined by source and target, requires a promotion piece.
        """
        move = chess.Move(self._source, self._target, chess.QUEEN)
        return move in self._board.legal_moves

    def _draw_promotion_choices(self):
        # mask the pawn
        if self._square_colour(self._source) == chess.WHITE:
            colour = self._colour_scheme.white
        else:
            colour = self._colour_scheme.black
        self._draw_square(self._source, colour)
        # draw the promotion choices
        promotion_dict = self._promotion_dict()
        piece_colour = self._board.turn
        for square, piece_type in promotion_dict.items():
            self._draw_square(square, self._colour_scheme.white_move_highlight)
            self._draw_piece(chess.Piece(piece_type, piece_colour), square)

    def _promotion_dict(self):
        file = chess.square_file(self._target)
        ranks = (7, 6, 5, 4) if self._board.turn == chess.WHITE else (0, 1, 2, 3)
        pieces = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
        return {chess.square(file, rank): piece for (rank, piece) in zip(ranks, pieces)}

    @staticmethod
    def _square_colour(square):
        if (chess.square_file(square) + chess.square_rank(square)) % 2 == 0:
            return chess.BLACK
        else:
            return chess.WHITE

    def _highlight_square(self, square: chess.Square):
        if self._square_colour(square) == chess.WHITE:
            colour = self._colour_scheme.white_highlight
        else:
            colour = self._colour_scheme.black_highlight
        self._draw_square(square, colour)
        piece = self._board.piece_at(square)
        if piece:
            self._draw_piece(piece, square)

    def _draw_square(self, square, colour: Tuple[int, int, int]):
        side = self._SQUARE_SIZE
        coordinates = self._get_coordinates(square)
        rect = pygame.Rect(*coordinates, self._SQUARE_SIZE, self._SQUARE_SIZE)
        pygame.draw.rect(self._screen, colour, rect)

    def _draw_piece(self, piece: chess.Piece, square: chess.Square):
        image = self._PIECE_IMAGES.get(piece)
        self._screen.blit(image, self._get_coordinates(square))

    def _get_square(self, coordinates: Tuple[int, int]) -> chess.Square:
        """
        Given coordinates, return the corresponding chess square.
        """
        x = coordinates[0] // self._SQUARE_SIZE
        y = coordinates[1] // self._SQUARE_SIZE

        if self._perspective == chess.WHITE:
            file = x
            rank = 7 - y
        else:
            file = 7 - x
            rank = y

        return chess.square(file, rank)

    def _get_coordinates(self, square: chess.Square) -> Tuple[int, int]:
        """
        Given a chess square, return the coordinates of its top-left corner.
        """
        rank = chess.square_rank(square)
        file = chess.square_file(square)

        if self._perspective == chess.WHITE:
            left = file * self._SQUARE_SIZE
            top = (7 - rank) * self._SQUARE_SIZE
        else:
            left = (7 - file) * self._SQUARE_SIZE
            top = rank * self._SQUARE_SIZE

        return (left, top)

    def _draw_squares(self):
        # the sqaures backdrop is always independent of the position and perspective
        # so just draw them
        for square in chess.SQUARES:
            square_colour = self._square_colour(square)
            if square_colour == chess.WHITE:
                colour = self._colour_scheme.white
            else:
                colour = self._colour_scheme.black
            self._draw_square(square, colour)

    def _highlight_move(self):
        """
        Highlight the squares corresponding to the last move.
        """
        if not self._board.move_stack:
            return
        move = self._board.peek()
        for square in (move.from_square, move.to_square):
            if self._square_colour(square) == chess.WHITE:
                colour = self._colour_scheme.white_move_highlight
            else:
                colour = self._colour_scheme.black_move_highlight
            self._draw_square(square, colour)

    def _draw_pieces(self):
        for square in chess.SQUARES:
            image = self._PIECE_IMAGES.get(self._board.piece_at(square))
            if image:
                self._screen.blit(image, self._get_coordinates(square))


if __name__ == "__main__":
    gui = ZugGUI()
    gui.setup_position(chess.Board())
    move = gui.get_move()
    print(move)
    gui.quit()
