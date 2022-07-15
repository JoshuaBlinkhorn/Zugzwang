import chess

class ZugBoard():

    def __init__(self, board: chess.Board):
        self._board = board
        self.perspective = board.turn # not sure why this is public

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
        ZugColour.WHITE: Fore.WHITE,
        ZugColour.BLACK: Fore.BLACK,        
    }

    @classmethod
    def _piece_colour_to_fore(cls, piece_colour):
        return cls.PIECE_COLOUR_TO_FORE.get(piece_colour)
        
    SQUARE_COLOUR_TO_BACK = {
        ZugColour.WHITE: Back.GREEN,
        ZugColour.BLACK: Back.CYAN,
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
            return ZugColour.WHITE
        else:
            return ZugColour.BLACK

    @classmethod
    def _square_index_by_row_and_col(cls, perspective):
        if perspective == ZugColour.WHITE:
            return lambda row, col: ((7 - row) * 8) + col
        else:
            return lambda row, col: (row * 8) + (7 - col)
                
    def make_string(self, perspective):
        square_index_by_row_and_col = self._square_index_by_row_and_col(perspective)
        string = ''
        for row in range(8):
            for col in range(8):
                square_index = square_index_by_row_and_col(row, col)
                square_colour = self._square_colour(square_index)
                piece = self._board.piece_map().get(square_index, None)
                piece_type = piece.piece_type if piece else None
                piece_colour = piece.color if piece else ZugColour.WHITE
                string += self._render_square(piece_type, piece_colour, square_colour)
            string += self._render_newline()
        return string
