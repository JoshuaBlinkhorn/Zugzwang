import chess

class ZugColours():
    WHITE = True
    BLACK = False
    

class ZugTrainingStatus():
    NEW = 'NEW'
    LEARNING_STAGE_1 = 'LEARNING_STAGE_1'
    LEARNING_STAGE_2 = 'LEARNING_STAGE_2'
    REVIEW = 'REVIEW'


class ZugPieces():
    KING = chess.KING
    QUEEN = chess.QUEEN
    ROOK = chess.ROOK
    BISHOP = chess.BISHOP
    KNIGHT = chess.KNIGHT    
    PAWN = chess.PAWN


class ZugDefaults():
    LEARNING_REMAINING = 10
    LEARNING_LIMIT = 10
    RECALL_FACTOR = 2
    RECALL_RADIUS = 3
    RECALL_MAX = 365




