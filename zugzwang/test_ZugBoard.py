import pytest
import chess
from colorama import Fore, Back, Style

from zugzwang import (
    ZugBoard,
    ZugPlayers,
    ZugPieceColours,
    ZugSquareColours,    
    ZugUnicodePieces,
    white_pieces
    )

@pytest.fixture
def mock_ZugBoard():
    return ZugBoard()


def test_ZugBoard_make_string_white_perspective(mock_ZugBoard):
    perspective = ZugPlayers.WHITE
    string = mock_ZugBoard.make_string(perspective)
    expected_char = Back.CYAN + Fore.BLACK + white_pieces[2]
    assert string.startswith(expected_char)


def test_ZugBoard_make_string_black_perspective(mock_ZugBoard):
    perspective = ZugPlayers.BLACK
    string = mock_ZugBoard.make_string(perspective)
    expected_char = Back.CYAN + Fore.WHITE + white_pieces[2]
    assert string.startswith(expected_char)


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
        mock_ZugBoard,
        piece_type,
        piece_colour,
        square_colour,
        expected_char
):
    rendered_char = mock_ZugBoard._render_square(
        piece_type,
        piece_colour,
        square_colour
    )
    assert rendered_char == expected_char
