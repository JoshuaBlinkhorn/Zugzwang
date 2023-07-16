import pygame
import chess

PIECE_IMAGES = {
    chess.Piece(chess.PAWN, chess.WHITE): pygame.image.load('img/white_pawn.png'),
    chess.Piece(chess.KNIGHT, chess.WHITE): pygame.image.load('img/white_knight.png'),
    chess.Piece(chess.BISHOP, chess.WHITE): pygame.image.load('img/white_bishop.png'),
    chess.Piece(chess.ROOK, chess.WHITE): pygame.image.load('img/white_rook.png'),
    chess.Piece(chess.QUEEN, chess.WHITE): pygame.image.load('img/white_queen.png'),
    chess.Piece(chess.KING, chess.WHITE): pygame.image.load('img/white_king.png'),    
    chess.Piece(chess.PAWN, chess.BLACK): pygame.image.load('img/black_pawn.png'),
    chess.Piece(chess.KNIGHT, chess.BLACK): pygame.image.load('img/black_knight.png'),
    chess.Piece(chess.BISHOP, chess.BLACK): pygame.image.load('img/black_bishop.png'),
    chess.Piece(chess.ROOK, chess.BLACK): pygame.image.load('img/black_rook.png'),
    chess.Piece(chess.QUEEN, chess.BLACK): pygame.image.load('img/black_queen.png'),
    chess.Piece(chess.KING, chess.BLACK): pygame.image.load('img/black_king.png'),
}

FLIP_IMAGE = pygame.transform.scale(pygame.image.load('img/flip.png'), (50, 50))
TICK_IMAGE = pygame.transform.scale(pygame.image.load('img/tick.png'), (50, 50))

