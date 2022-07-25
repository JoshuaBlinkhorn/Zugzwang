import pytest
import chess
from colorama import Fore, Back, Style

from zugzwang.board import ZugBoard, ZugUnicodePieces
from zugzwang.constants import ZugColours, ZugPieces

WHITE_PERSPECTIVE_TOP_ROW = (
    (ZugPieces.ROOK, ZugColours.BLACK, ZugColours.WHITE),
    (ZugPieces.KNIGHT, ZugColours.BLACK, ZugColours.BLACK),
    (ZugPieces.BISHOP, ZugColours.BLACK, ZugColours.WHITE),
    (ZugPieces.QUEEN, ZugColours.BLACK, ZugColours.BLACK),
    (ZugPieces.KING, ZugColours.BLACK, ZugColours.WHITE),
    (ZugPieces.BISHOP, ZugColours.BLACK, ZugColours.BLACK),
    (ZugPieces.KNIGHT, ZugColours.BLACK, ZugColours.WHITE),
    (ZugPieces.ROOK, ZugColours.BLACK, ZugColours.BLACK),
)

BLACK_PERSPECTIVE_TOP_ROW = (
    (ZugPieces.ROOK, ZugColours.WHITE, ZugColours.WHITE),
    (ZugPieces.KNIGHT, ZugColours.WHITE, ZugColours.BLACK),
    (ZugPieces.BISHOP, ZugColours.WHITE, ZugColours.WHITE),
    (ZugPieces.KING, ZugColours.WHITE, ZugColours.BLACK),
    (ZugPieces.QUEEN, ZugColours.WHITE, ZugColours.WHITE),
    (ZugPieces.BISHOP, ZugColours.WHITE, ZugColours.BLACK),
    (ZugPieces.KNIGHT, ZugColours.WHITE, ZugColours.WHITE),
    (ZugPieces.ROOK, ZugColours.WHITE, ZugColours.BLACK),
)

@pytest.mark.parametrize(
    'top_row, perspective',
    [
        (WHITE_PERSPECTIVE_TOP_ROW, ZugColours.WHITE),
        (BLACK_PERSPECTIVE_TOP_ROW, ZugColours.BLACK),
    ]
)
def test_ZugBoard_make_string(top_row, perspective):
    prefix = ''
    for (piece_type, piece_colour, square_colour) in top_row:
        prefix += ZugBoard._render_square(
            piece_type, piece_colour, square_colour
        )
    prefix += ZugBoard._render_newline()
    assert ZugBoard(chess.Board()).make_string(perspective).startswith(prefix)


@pytest.mark.parametrize(
    'piece_type, piece_colour, square_colour, expected_char',
    [
        (
            chess.ROOK,
            ZugColours.WHITE,
            ZugColours.WHITE,
            Back.GREEN + Fore.WHITE + ZugUnicodePieces.ROOK            
        ),
        (
            chess.BISHOP,
            ZugColours.WHITE,
            ZugColours.BLACK,
            Back.CYAN + Fore.WHITE + ZugUnicodePieces.BISHOP            
        ),
        (
            chess.QUEEN,
            ZugColours.BLACK,
            ZugColours.WHITE,
            Back.GREEN + Fore.BLACK + ZugUnicodePieces.QUEEN            
        ),
        (
            chess.KING,
            ZugColours.BLACK,
            ZugColours.BLACK,
            Back.CYAN + Fore.BLACK + ZugUnicodePieces.KING            
        ),
        (
            chess.ROOK,
            ZugColours.BLACK,
            ZugColours.BLACK,
            Back.CYAN + Fore.BLACK + ZugUnicodePieces.ROOK            
        ),
        (
            chess.PAWN,
            ZugColours.WHITE,
            ZugColours.WHITE,
            Back.GREEN + Fore.WHITE + ZugUnicodePieces.PAWN            
        ),
        (
            None,
            ZugColours.WHITE,
            ZugColours.WHITE,
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
