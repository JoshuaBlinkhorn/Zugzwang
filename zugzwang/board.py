import chess
from colorama import Fore, Back, Style

from zugzwang.constants import ZugPieces, ZugColours


class ZugUnicodePieces():
    KING = '\u2654'
    QUEEN = '\u2655'
    ROOK = '\u2656'
    BISHOP = '\u2657'
    KNIGHT = '\u2658'        
    PAWN = '\u2659'    


class ZugBoard():

    def __init__(self, board: chess.Board):
        self._board = board

    PIECE_TYPE_TO_UNICODE = {
        ZugPieces.KING: ZugUnicodePieces.KING,
        ZugPieces.QUEEN: ZugUnicodePieces.QUEEN,
        ZugPieces.ROOK: ZugUnicodePieces.ROOK,
        ZugPieces.BISHOP: ZugUnicodePieces.BISHOP,
        ZugPieces.KNIGHT: ZugUnicodePieces.KNIGHT,
        ZugPieces.PAWN: ZugUnicodePieces.PAWN,
    }

    @classmethod
    def _piece_type_to_unicode(cls, piece_type):
        return cls.PIECE_TYPE_TO_UNICODE.get(piece_type, ' ')
        
    PIECE_COLOUR_TO_FORE = {
        ZugColours.WHITE: Fore.WHITE,
        ZugColours.BLACK: Fore.BLACK,        
    }

    @classmethod
    def _piece_colour_to_fore(cls, piece_colour):
        return cls.PIECE_COLOUR_TO_FORE.get(piece_colour)
        
    SQUARE_COLOUR_TO_BACK = {
        ZugColours.WHITE: Back.GREEN,
        ZugColours.BLACK: Back.CYAN,
    }

    @classmethod
    def _square_colour_to_back(cls, square_colour):
        return cls.SQUARE_COLOUR_TO_BACK.get(square_colour)
        
    @classmethod
    def _render_square(cls, piece_type, piece_colour, square_colour):
        fore = cls._piece_colour_to_fore(piece_colour)
        back = cls._square_colour_to_back(square_colour)
        piece = cls._piece_type_to_unicode(piece_type)
        return back + fore + piece

    @classmethod
    def _render_newline(cls):
        return Style.RESET_ALL + '\n'
    
    @classmethod
    def _square_colour(cls, square):
        if (chess.square_rank(square) + chess.square_file(square)) % 2:
            return ZugColours.WHITE
        else:
            return ZugColours.BLACK

    @classmethod
    def _square_index_by_row_and_col(cls, perspective):
        if perspective == ZugColours.WHITE:
            return lambda row, col: ((7 - row) * 8) + col
        else:
            return lambda row, col: (row * 8) + (7 - col)
                
    def make_string(self, perspective: bool, margin=20):
        square_index_by_row_and_col = self._square_index_by_row_and_col(perspective)
        string = ''
        for row in range(8):
            string += ' ' * margin
            for col in range(8):
                square_index = square_index_by_row_and_col(row, col)
                square_colour = self._square_colour(square_index)
                piece = self._board.piece_map().get(square_index, None)
                piece_type = piece.piece_type if piece else None
                piece_colour = piece.color if piece else ZugColours.WHITE
                string += self._render_square(piece_type, piece_colour, square_colour)
                string += ' '
            string += self._render_newline()
        return string

    def make_string_with_margin(self, perspective: bool, margin_width=10):
        margin = '' * margin_width
        board = self.make_string(perspective)
        return (margin + board.replace('\n','\n' + margin))[:-margin_width]

