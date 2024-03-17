import chess

# TODO (non-critical):
#
# 1. Do some of these constants belong in specific modules?
#    - ZugPieces is only used in board.py
#    - ZugTrainingStatuses is only used by ZugTrainingPosition and its presenter
#    - ZugDefaults is only used by the ZugRoot constructor
#    - ZugSolutionStatuses may only be used by ZugSolution..
#    That leaves just ZugColours, which makes sense, as the only truly generic
#    constants here.
#
# 2. It would be nice to do perspective.switch(); i.e. let's have a class ZugColour
#    and ZugBlack and ZugWhite as instances, which support that method.


class ZugColours:
    WHITE = True
    BLACK = False


class ZugSolutionStatuses:
    LEARNED = "LEARNED"
    UNLEARNED = "UNLEARNED"


class ZugPieces:
    KING = chess.KING
    QUEEN = chess.QUEEN
    ROOK = chess.ROOK
    BISHOP = chess.BISHOP
    KNIGHT = chess.KNIGHT
    PAWN = chess.PAWN
