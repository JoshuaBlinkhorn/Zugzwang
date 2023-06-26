from __future__ import annotations

import pygame
import chess
from typing import List


_SQUARE_SIZE = 60
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

_THEME = ColourScheme(
    white = (237, 220, 180),
    black = (180, 134, 100),
    white_highlight = (113, 143, 101),
    black_highlight = (99, 117, 81),
    white_move_highlight = (190, 198, 100),
    black_move_highlight = (158, 156, 40),       
)

_PIECE_IMAGES = {
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

_FLIP_IMAGE = pygame.transform.scale(pygame.image.load('img/flip.png'), (50, 50))
_TICK_IMAGE = pygame.transform.scale(pygame.image.load('img/tick.png'), (50, 50))

class ZugSceneElement:
    def __init__(self, scene: ZugScene, rect: pygame.Rect):
        self._scene = scene
        self.rect = rect

    def clicked(self):
        print("I'm an element and you just clicked me.")

    def draw(self, screen: pygame.Surface):
        pass


class ZugSetupSquare(ZugSceneElement):
    def __init__(self, scene: ZugScene, rect: pygame.Rect, colour: bool):
        super().__init__(scene, rect)
        self._colour = colour
        self._piece = None
        self._highlighted = False

    def highlight(self):
        self._highlighted = True

    def unhighlight(self):
        self._highlighted = False

    def draw(self, screen: pygame.Surface):
        colour = self._get_background_colour()        
        pygame.draw.rect(screen, colour, self.rect)
        if self._piece is not None:
            screen.blit(_PIECE_IMAGES.get(self._piece), (self.rect.x, self.rect.y))

    def clicked(self):
        selected_piece = self._scene.get_selection()
        if self._piece == selected_piece:
            self._piece = None
        else:
            self._piece = self._scene.get_selection()

    def get_piece(self):
        return self._piece

    def _get_background_colour(self):
        if self._highlighted:
            return _THEME.white_highlight if self._colour == chess.WHITE \
                else _THEME.black_highlight
        else:
            return _THEME.white if self._colour == chess.WHITE else _THEME.black


class ZugSelectorElement(ZugSceneElement):
    def __init__(
            self,
            scene: ZugSetupPositionScene,
            rect: pygame.Rect,
            colour: bool,            
            selection: Union[chess.Piece(), str],

    ):
        super().__init__(scene, rect)
        self._colour = colour
        self._selection = selection
        self._highlighted = False

    def draw(self, screen: pygame.Surface):
        colour = self._get_background_colour()
        pygame.draw.rect(screen, colour, self.rect)
        if type(self._selection) == chess.Piece:
            image = _PIECE_IMAGES.get(self._selection)
        elif type(self._selection) == str:
            image = self._font.render(self._selection, True, (0,0,0))
        screen.blit(image, image.get_rect(center=self.rect.center))
            

    def highlight(self):
        self._highlighted = True

    def unhighlight(self):
        self._highlighted = False

    def get_selection(self):
        return self._selection
        
    def clicked(self):
        pass
        
    def _get_background_colour(self):
        if self._highlighted:
            return _THEME.white_highlight if self._colour == chess.WHITE \
                else _THEME.black_highlight
        else:
            return _THEME.white if self._colour == chess.WHITE else _THEME.black

        
class ZugTextField(ZugSceneElement):

    _FONT_COLOUR = _THEME.white

    def __init__(self, scene: ZugScene, rect: pygame.Rect, caption: str):
        super().__init__(scene, rect)
        self._caption = caption
        self._font = pygame.font.SysFont(None, 24)
    
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, _THEME.white, self.rect)
        image = self._font.render(self._caption, True, (0, 0, 0))
        screen.blit(image, (self.rect.x + 5, self.rect.y + 5))

    def clicked(self):
        pass

    def set_caption(self, caption):
        self._caption = caption


class ZugTurnButton(ZugSceneElement):
    def clicked(self):
        self._scene.toggle_turn()

    def draw(self, screen: pygame.Surface):
        colour = _THEME.white
        pygame.draw.rect(screen, colour, self.rect)
        piece = chess.Piece(chess.KING, self._scene.get_turn())
        screen.blit(_PIECE_IMAGES.get(piece), (self.rect.x, self.rect.y))


        
class ZugFlipButton(ZugSceneElement):

    def clicked(self):
        self._scene.toggle_perspective()

    def draw(self, screen: pygame.Surface):
        colour = _THEME.black
        pygame.draw.rect(screen, colour, self.rect)
        piece = chess.Piece(chess.KING, self._scene.get_turn())
        screen.blit(_FLIP_IMAGE, (self.rect.x + 5, self.rect.y + 5))


class ZugClearButton(ZugSceneElement):
    def clicked(self):
        self._scene.clear()

    def draw(self, screen: pygame.Surface):
        for i in range(8):
            for j in range(8):
                colour = _THEME.white if (i + j) % 2 == 0 else _THEME.black
                x = self.rect.x + (i * _SQUARE_SIZE) // 8
                y = self.rect.y + (j * _SQUARE_SIZE) // 8
                x1 = self.rect.x + ((i + 1) * _SQUARE_SIZE) // 8
                y1 = self.rect.y + ((j + 1) * _SQUARE_SIZE) // 8                
                
                rect = pygame.Rect(x, y, x1 - x, y1 - y)
                pygame.draw.rect(screen, colour, rect)

class ZugTickButton(ZugSceneElement):

    def __init__(self, scene: ZugScene, rect: pygame.Rect):    
        super().__init__(scene, rect)
        self._active = False
    
    def clicked(self):
        if self._active is True:
            self._scene.done()

    def set_active(self):
        self._active = True
        
    def set_inactive(self):
        self._active = False
        
    def draw(self, screen: pygame.Surface):
        colour = _THEME.black
        pygame.draw.rect(screen, colour, self.rect)
        piece = chess.Piece(chess.KING, self._scene.get_turn())
        if self._active is True:
            screen.blit(_TICK_IMAGE, (self.rect.x + 5, self.rect.y + 5))


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



class ZugSetupPositionScene(ZugScene):

    _CASTLING_RIGHTS = {
        0: 'Q',
        7: 'K',
        56: 'q',
        63: 'k',
    }
    _EN_PASSENT_CAPTURES = {
        24: [25],
        25: [24, 26],
        26: [25, 27],
        27: [26, 28],
        28: [27, 29],
        29: [28, 30],
        30: [29, 31],
        31: [30],
        32: [33],
        33: [32, 34],
        34: [33, 35],
        35: [34, 36],
        36: [35, 37],
        37: [36, 38],
        38: [37, 39],
        39: [38],
    }
    _EN_PASSENT_MAP = {
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

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self._perspective = chess.WHITE
        self._selection = None
        self._selector = {}
        self._elements_to_squares = {}
        self._squares_to_elements = {}        

        self._turn = chess.WHITE
        self._castling_rights = {
            0: False,
            7: False,
            56: False,
            63: False,
        }
        self._en_passent = None
        self._fen_element = None
        self._tick_button = None

        # board
        BOARD_X = 180
        BOARD_Y = 80
        for i in range(8):
            for j in range(8):
                x = BOARD_X + (j * _SQUARE_SIZE)
                y = BOARD_Y + (i * _SQUARE_SIZE)
                rect = pygame.Rect(x, y, _SQUARE_SIZE, _SQUARE_SIZE)
                colour = chess.WHITE if (i + j) % 2 == 0 else chess.BLACK
                element = ZugSetupSquare(self, rect, colour)
                self.add_element(element)
                square = ((7 - i) * 8) + j
                self._elements_to_squares[element] = square 
                self._squares_to_elements[square] = element

        # piece selector
        PS_X = BOARD_X + _SQUARE_SIZE
        PS_Y = BOARD_Y + (9 * _SQUARE_SIZE)
        for row, piece_colour in enumerate((chess.WHITE, chess.BLACK)):
            for column, piece_type in enumerate(
                (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                 chess.ROOK, chess.QUEEN, chess.KING)
            ):
                x = PS_X + (column * _SQUARE_SIZE)
                y = PS_Y + (row * _SQUARE_SIZE)
                rect = pygame.Rect(x, y, _SQUARE_SIZE, _SQUARE_SIZE)
                colour = chess.BLACK if (row + column) % 2 == 0 else chess.WHITE
                piece = chess.Piece(piece_type, piece_colour)
                selectable = ZugSelectorElement(self, rect, colour, piece)
                self.add_element(selectable)
                self._selector[piece] = selectable

        # options
        OPT_X = BOARD_X - (2 * _SQUARE_SIZE)
        OPT_Y = BOARD_Y
        rect = pygame.Rect(OPT_X, OPT_Y, _SQUARE_SIZE, _SQUARE_SIZE)
        self.add_element(ZugTurnButton(self, rect))
        rect = pygame.Rect(OPT_X, OPT_Y + (_SQUARE_SIZE), _SQUARE_SIZE, _SQUARE_SIZE)
        self.add_element(ZugFlipButton(self, rect))
        rect = pygame.Rect(OPT_X, OPT_Y + (2 * _SQUARE_SIZE), _SQUARE_SIZE, _SQUARE_SIZE)
        self.add_element(ZugClearButton(self, rect))

        # fen
        FEN_X = BOARD_X + (9 * _SQUARE_SIZE)
        FEN_Y = BOARD_Y + (3 * _SQUARE_SIZE)
        rect = pygame.Rect(FEN_X, FEN_Y, (8 * _SQUARE_SIZE), _SQUARE_SIZE)
        self._fen_element = ZugTextField(self, rect, self._fen())
        self.add_element(self._fen_element)
        TICK_X = FEN_X + (3.5 * _SQUARE_SIZE) 
        TICK_Y = FEN_Y + (2 * _SQUARE_SIZE)       
        rect = pygame.Rect(TICK_X, TICK_Y, _SQUARE_SIZE, _SQUARE_SIZE)
        self._tick_button = ZugTickButton(self, rect)
        self.add_element(self._tick_button)

    def _flip_perspective(self):
        return
        self._perspective = not self._perspective
        elements_to_squares = {
            element: self._rotate(square)
            for element, square in self._elements_to_squares.items()
        }
        squares_to_elements = {
            square: self._squares_to_elements(self._rotate(square))
            for square, element in self._squares_to_elements.items()
        }
        self._elements_to_squares = elements_to_squares
        self._squares_to_elements = squares_to_elements

    @staticmethod
    def _rotate(square: chess.Square) -> chess.Square:
        return 63 - square        
        
    def clear(self):
        self._selection = None
        for element in self._elements_to_squares.keys():
            element.clicked()

    def toggle_turn(self):
        self._turn = not self._turn

    def get_turn(self):
        return self._turn

    def toggle_perspective(self):
        self._perspective = not self._perspective

    def _fen(self):
        board = self._board_fen()
        turn = 'w' if self._turn == chess.WHITE else 'b'
        rights = self._castling_rights_fen()
        en_passent = self._en_passent_fen()
        halfmove = '0'
        fullmove = '1'
        return ' '.join([board, turn, str(rights), en_passent, halfmove, fullmove])

    def _board_fen(self):
        fen = ''
        for r in range(8):
            for f in range(8):
                piece = self._squares_to_elements[((7-r) * 8) + f].get_piece()
                symbol = piece.symbol() if piece is not None else " "
                fen = fen + symbol
            fen += '/'
        fen = fen[:-1]
        for i in range(8, 0, -1):
            fen = fen.replace((' ' * i), str(i))
        return fen

    def _en_passent_fen(self):
        if self._en_passent is None:
            return '-'
        return chess.square_name(self._EN_PASSENT_MAP[self._en_passent])

    def _castling_rights_fen(self):
        rights = ''.join(
            [
                self._CASTLING_RIGHTS[square]
                for square in self._castling_rights
                if self._castling_rights[square]
            ]
        )
        return rights if rights != '' else '-'

    def get_selection(self):
        return self._selection

    def set_selection(self, piece: chess.Piece):
        self._selection = piece

    def _click_registered(self, element):
        if element in self._selector.values():
            if element.get_selection() == self._selection:
                element.unhighlight()
                self._selection = None
            else:
                if self._selection is not None:
                    self._selector[self._selection].unhighlight()
                self._selection = element.get_selection()
                element.highlight()

        element.clicked()

        for square in self._CASTLING_RIGHTS:
            if not self._can_set_castling_right(square):
                self._squares_to_elements[square].unhighlight()

        if self._en_passent and not self._can_set_en_passent(self._en_passent):
            self._squares_to_elements[self._en_passent].unhighlight()
            self._en_passent = None

        fen = self._fen()
        self._fen_element.set_caption(fen)
        if chess.Board(fen).is_valid():
            self._tick_button.set_active()
        else:
            self._tick_button.set_inactive()
                
    def _right_click_registered(self, element):
        if element in self._elements_to_squares.keys():
            square = self._elements_to_squares[element]
            # castling rights
            if square in self._CASTLING_RIGHTS:
                if self._castling_rights[square]:
                    element.unhighlight()
                    self._castling_rights[square] = False
                else:
                    if self._can_set_castling_right(square):
                        element.highlight()
                        self._castling_rights[square] = True

            elif self._can_set_en_passent(square):
                if square == self._en_passent:
                    self._en_passent = None
                else:
                    if self._en_passent is not None:
                        self._squares_to_elements[self._en_passent].unhighlight()
                    self._squares_to_elements[square].highlight()
                    self._en_passent = square                        

        fen = self._fen()
        self._fen_element.set_caption(fen)
        if chess.Board(fen).is_valid():
            self._tick_button.set_active()
        else:
            self._tick_button.set_inactive()

    def _can_set_castling_right(self, square: chess.Square):
        e1_element = self._squares_to_elements[4]
        white_king = e1_element.get_piece() == chess.Piece(chess.KING, chess.WHITE)
        e8_element = self._squares_to_elements[60]
        black_king = e8_element.get_piece() == chess.Piece(chess.KING, chess.BLACK)
        current_piece = self._squares_to_elements[square].get_piece()
        if square == 0 or square == 7:
            return white_king and current_piece == chess.Piece(chess.ROOK, chess.WHITE)
        else:
            return black_king and current_piece == chess.Piece(chess.ROOK, chess.BLACK)

    def _can_set_en_passent(self, square: chess.Square):
        if self._turn == chess.WHITE and square not in range(32,39):
            return False
        if self._turn == chess.BLACK and square not in range(24,31):
            return False
        white_pawn = chess.Piece(chess.PAWN, chess.WHITE)
        black_pawn = chess.Piece(chess.PAWN, chess.BLACK)
        capturing_piece = white_pawn if self._turn == chess.WHITE else black_pawn
        captured_piece = black_pawn if self._turn == chess.WHITE else white_pawn
        return (
            self._squares_to_elements[square].get_piece() == captured_piece
            and any(
                self._squares_to_elements[capturer].get_piece() == capturing_piece
                for capturer in self._EN_PASSENT_CAPTURES[square]
            )
        )

    def _square_to_index(self, square: chess.Square):
        rank = chess.square_rank(square)
        fle = chess.square_file(square)
        if self._perspective is chess.WHITE:
            index = 64 - ((rank + 1) * 8) + fle
        else:
            index = (7 - fle) + (8 * rank)
        return index

    def _get_square(self, element):
        index = self._squares.index(element)
        x = index // 8
        y = index % 8
        if self._perspective is chess.WHITE:
            square =  ((7 - y) * 8) + x
        else:
            square = (7 - x) + (8 * y)
        return square


    def _regress(self):
        if self._level < self._ENTER:
            return
        self._level -= 1
        self._update_caption()
        if self._level == self._ENTER:
            self.backout()

    def _progress(self):
        if self._level > self._EXIT:
            return        
        self._level += 1
        self._update_caption()
        if self._level == self._EXIT:
            self.complete()

    def _update_caption(self):
        self._caption_field.set_caption(self._CAPTIONS.get(self._level, ""))        
            
    def backout(self):
        pass

    def done(self):
        pass
        
        
class ZugDisplay:

    def __init__(self):
        self._scenes = []
        self._scene = None
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        self._screen = pygame.display.set_mode([width, height], pygame.FULLSCREEN)

    def get_screen(self):
        return self._screen
        
    def add_scene(self, scene: ZugScene):
        self._scenes.append(scene)

    def set_scene(self, scene: ZugScene):
        self._scene = scene

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
                self._scene.draw()

            clock.tick(30)                
            pygame.display.flip()

class ZugFenCreatorModel:
    def __init__(self):
        self._board = {square: None for square in chess.SQUARES}
        self.turn = chess.WHITE
        self.perspective = chess.WHITE
        self.piece = None
        self.ep = None
        self._castling = {
            'K': False,
            'Q': False,
            'k': False,
            'q': False,
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
            
    def toggle_castling(self, symbol: str):
        self._castling[symbol] = not self._castling[symbol]

    def set_castling(self, symbol: str, value: bool):
        self._castling[symbol] = value

    def is_valid(self) -> bool:
        return chess.board(self.fen()).is_valid()
            
    def fen(self) -> str:
        board = self._board_fen()
        turn = 'w' if self._turn == chess.WHITE else 'b'
        castling = self._castling_fen()
        ep = self._en_fen()
        halfmove = '0'
        fullmove = '1'
        return ' '.join([board, turn, rights, ep, halfmove, fullmove])

    def _board_fen(self):
        fen = ''
        for rank in range(8):
            for fle in range(8):
                piece = self._board[((7 - rank) * 8) + fle]
                symbol = piece.symbol() if piece is not None else " "
                fen = fen + symbol
            fen += '/'
        fen = fen[:-1]
        for i in range(8, 0, -1):
            fen = fen.replace((' ' * i), str(i))
        return fen

    def _ep_fen(self):
        return '-' if self.ep else chess.square_name(self.ep)

    def _castling_fen(self):
        castling = ''.join([c for c in self._castling if self._castling[c]])
        return castling if castling else '-'

class ZugFenCreatorView:
    def __init__(self):
        # board
        l = 180
        t = 80
        self.board = {}
        for row in range(8):
            for column in range(8):
                x = l + (column * _SQ_SIZE)
                y = t + (row * _SQ_SIZE)
                rect = pygame.Rect(x, y, _SQ_SIZE, _SQ_SIZE)
                colour = chess.WHITE if (i + j) % 2 == 0 else chess.BLACK
                self.board[(row, column)] = ZugSquareView(self, rect, colour)

        # piece selector
        l = 720
        t = 260
        self.selector = {}
        for row, piece_colour in enumerate((chess.WHITE, chess.BLACK)):
            for column, piece_type in enumerate(
                (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                 chess.ROOK, chess.QUEEN, chess.KING)
            ):
                x = l + (column * _SQ_SIZE)
                y = t + (row * _SQ_SIZE)
                rect = pygame.Rect(x, y, _SQ_SIZE, _SQ_SIZE)
                colour = chess.WHITE if (row + column) % 2 == 0 else chess.BLACK
                piece = chess.Piece(piece_type, piece_colour)
                self.selector[piece] = ZugSquareView(self, rect, colour, piece)

        # thumbs
        l = 60
        t = 80
        rect = pygame.Rect(l, t, _SQ_SIZE, _SQ_SIZE)
        self.turn = ZugTurnView(self, rect)
        rect = pygame.Rect(l, t + (_SQ_SIZE), _SQ_SIZE, _SQ_SIZE)
        self.flip = ZugFlipView(self, rect)
        rect = pygame.Rect(l, t + (2 * _SQ_SIZE), _SQ_SIZE, _SQ_SIZE)
        self.clear = ZugClearView(self, rect)

        # fen
        l = 180
        t = 800
        rect = pygame.Rect(l, t, _SQ_SIZE * 7, _SQ_SIZE)
        self.fen = ZugTextView(self, rect)
        rect = pygame.Rect(l + (7 * _SQ_SIZE), t, _SQ_SIZE, _SQ_SIZE)


class ZugSquareView:
    def __init__(
            self,
            rect: pygame.Rect,
            colour: chess.Color,
            piece: Optional[chess.Piece]=None
    ):
        self._colour = colour
        self._piece = piece
        self._highlighted = False

    def set_highlight(self, highlighted: bool):
        self._highlighted = higlighted

    def set_piece(self, piece: Optional[chess.Piece]):
        self._piece = piece

    def draw(self, screen: pygame.Surface):
        colour = self._background_colour()        
        pygame.draw.rect(screen, colour, self.rect)
        if self._piece is not None:
            screen.blit(_PIECE_IMAGES.get(self._piece), (self.rect.x, self.rect.y))

    def _background_colour(self):
        if self._highlighted:
            return _THEME.white_highlight if self._colour == chess.WHITE \
                else _THEME.black_highlight
        else:
            return _THEME.white if self._colour == chess.WHITE else _THEME.black


class ZugTurnView:
    def __init__(self, rect: pygame.Rect):
        self._rect = rect
        self._turn = chess.WHITE

    def set_turn(self, turn: chess.Color):
        self._turn = turn

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, _THEME.white, self.rect)
        piece = chess.Piece(chess.KING, self._turn)
        screen.blit(_PIECE_IMAGES.get(piece), (self.rect.x, self.rect.y))


class ZugFlipView:
    def __init__(self, rect: pygame.Rect):
        self._rect = rect

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, _THEME.black, self.rect)
        screen.blit(_FLIP_IMAGE, (self.rect.x + 5, self.rect.y + 5))


class ZugClearView:
    def __init__(self, rect: pygame.Rect):
        self._rect = rect

    def draw(self, screen: pygame.Surface):
        for i in range(8):
            for j in range(8):
                colour = _THEME.white if (i + j) % 2 == 0 else _THEME.black
                x = self.rect.x + (i * _SQ_SIZE) // 8
                y = self.rect.y + (j * _SQ_SIZE) // 8
                x1 = self.rect.x + ((i + 1) * _SQ_SIZE) // 8
                y1 = self.rect.y + ((j + 1) * _SQ_SIZE) // 8
                rect = pygame.Rect(x, y, x1 - x, y1 - y)
                pygame.draw.rect(screen, colour, rect)
                

class ZugTextView:
    def __init__(self, rect: pygame.Rect, caption: str=None):
        self.rect = rect
        self._caption = caption
        self._font = pygame.font.SysFont(None, 24)
    
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, _THEME.white, self.rect)
        if self._caption:
            image = self._font.render(self._caption, True, (0, 0, 0))
            screen.blit(image, (self.rect.x + 5, self.rect.y + 5))

    def set_caption(self, caption):
        self._caption = caption


class ZugTickView:

    def __init__(self, rect: pygame.Rect):    
        self._rect = rect
        self._active = False
    
    def set_active(self):
        self._active = True
        
    def set_inactive(self):
        self._active = False
        
    def draw(self, screen: pygame.Surface):
        colour = _THEME.black
        pygame.draw.rect(screen, colour, self.rect)
        if self._active is True:
            screen.blit(_TICK_IMAGE, (self.rect.x + 5, self.rect.y + 5))


                
if __name__ == '__main__':
    pygame.init()    
    display = ZugDisplay()
    setup_scene = ZugSetupPositionScene(display.get_screen())
    display.add_scene(setup_scene)
    display.set_scene(setup_scene)
    display.main()
