import pytest
import chess
from colorama import Fore, Back, Style

from zugzwang import (
    ZugBoard,
    ZugPlayers,
    ZugPieceColours,
    ZugSquareColours,
    ZugPieces,
    ZugUnicodePieces,
)

@pytest.fixture
def mock_ZugBoard():
    return ZugBoard()

WHITE_PERSPECTIVE_TOP_ROW = (
    (ZugPieces.ROOK, ZugPieceColours.BLACK, ZugSquareColours.WHITE),
    (ZugPieces.KNIGHT, ZugPieceColours.BLACK, ZugSquareColours.BLACK),
    (ZugPieces.BISHOP, ZugPieceColours.BLACK, ZugSquareColours.WHITE),
    (ZugPieces.QUEEN, ZugPieceColours.BLACK, ZugSquareColours.BLACK),
    (ZugPieces.KING, ZugPieceColours.BLACK, ZugSquareColours.WHITE),
    (ZugPieces.BISHOP, ZugPieceColours.BLACK, ZugSquareColours.BLACK),
    (ZugPieces.KNIGHT, ZugPieceColours.BLACK, ZugSquareColours.WHITE),
    (ZugPieces.ROOK, ZugPieceColours.BLACK, ZugSquareColours.BLACK),
)

BLACK_PERSPECTIVE_TOP_ROW = (
    (ZugPieces.ROOK, ZugPieceColours.WHITE, ZugSquareColours.WHITE),
    (ZugPieces.KNIGHT, ZugPieceColours.WHITE, ZugSquareColours.BLACK),
    (ZugPieces.BISHOP, ZugPieceColours.WHITE, ZugSquareColours.WHITE),
    (ZugPieces.KING, ZugPieceColours.WHITE, ZugSquareColours.BLACK),
    (ZugPieces.QUEEN, ZugPieceColours.WHITE, ZugSquareColours.WHITE),
    (ZugPieces.BISHOP, ZugPieceColours.WHITE, ZugSquareColours.BLACK),
    (ZugPieces.KNIGHT, ZugPieceColours.WHITE, ZugSquareColours.WHITE),
    (ZugPieces.ROOK, ZugPieceColours.WHITE, ZugSquareColours.BLACK),
)

@pytest.mark.parametrize(
    'top_row, perspective',
    [
        (WHITE_PERSPECTIVE_TOP_ROW, ZugPlayers.WHITE),
        (BLACK_PERSPECTIVE_TOP_ROW, ZugPlayers.BLACK),
    ]
)
def test_ZugBoard_make_string(top_row, perspective):
    board = ZugBoard()
    prefix = ''
    for (piece_type, piece_colour, square_colour) in top_row:
        prefix += ZugBoard._render_square(
            piece_type, piece_colour, square_colour
        )
    prefix += ZugBoard._render_newline()
    assert ZugBoard().make_string(perspective).startswith(prefix)


@pytest.mark.parametrize(
    'piece_type, piece_colour, square_colour, expected_char',
    [
        (
            chess.ROOK,
            ZugPieceColours.WHITE,
            ZugSquareColours.WHITE,
            Back.GREEN + Fore.WHITE + ZugUnicodePieces.ROOK            
        ),
        (
            chess.BISHOP,
            ZugPieceColours.WHITE,
            ZugSquareColours.BLACK,
            Back.CYAN + Fore.WHITE + ZugUnicodePieces.BISHOP            
        ),
        (
            chess.QUEEN,
            ZugPieceColours.BLACK,
            ZugSquareColours.WHITE,
            Back.GREEN + Fore.BLACK + ZugUnicodePieces.QUEEN            
        ),
        (
            chess.KING,
            ZugPieceColours.BLACK,
            ZugSquareColours.BLACK,
            Back.CYAN + Fore.BLACK + ZugUnicodePieces.KING            
        ),
        (
            chess.ROOK,
            ZugPieceColours.BLACK,
            ZugSquareColours.BLACK,
            Back.CYAN + Fore.BLACK + ZugUnicodePieces.ROOK            
        ),
        (
            chess.PAWN,
            ZugPieceColours.WHITE,
            ZugSquareColours.WHITE,
            Back.GREEN + Fore.WHITE + ZugUnicodePieces.PAWN            
        ),
        (
            None,
            ZugPieceColours.WHITE,
            ZugSquareColours.WHITE,
            Back.GREEN + Fore.WHITE + ' '
        ),
    ]
)
def test_ZugBoard_render_square(
        piece_type,
        piece_colour,
        square_colour,
        expected_char
):
    rendered_char = ZugBoard._render_square(piece_type, piece_colour, square_colour)
    assert rendered_char == expected_char
