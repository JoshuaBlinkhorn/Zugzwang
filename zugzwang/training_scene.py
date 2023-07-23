from __future__ import annotations

from typing import Dict, Any
import os
import chess
import pygame
import time

from zugzwang.group import Chapter
from zugzwang.display import ZugDisplay
from zugzwang.scene import (
    ZugScene,
    ZugSceneView,
    ZugSceneModel,
)
from zugzwang.view import (
    ZugView,
    ZugTextView,
    ZugViewGroup,
)
from zugzwang.graphics import PIECE_IMAGES
from zugzwang.palette import DEFAULT_THEME as THEME
from zugzwang.training import PositionTrainer

class ZugTrainingScene(ZugScene):

    _AWAITING_SOURCE = "AWAITING SOURCE"
    _AWAITING_TARGET = "AWAITING TARGET"
    _AWAITING_PROMOTION = "AWAITING PROMOTION"

    def __init__(self, display: ZugDisplay, chapters: List[Chapter]):
        # Scene MVC setup
        model = ZugTrainingModel()
        width = display.get_screen().get_width()
        height = display.get_screen().get_height()
        view = ZugTrainingView(width, height)
        super().__init__(display, model, view)

        # misc - this should be part of the model?
        self._failure = False
        self._source = None
        self._target = None
        self._status = self._AWAITING_SOURCE
        self._chapters = chapters
        self._chapter = self._chapters.pop(0)

        # setup the training session for the first chapter
        self._trainer = PositionTrainer(self._chapter)
        self._position = self._trainer.pop()
        self._present_problem()

    def _left_click_registered(self, view_id: str):
        print("CLICKED:", view_id)
        if view_id == 'logo':
            self._display.pop_scene()
            return

        if view_id.startswith('board.'):
            square_name = view_id.split('.')[-1]
            square = chess.parse_square(square_name)
            if self._status == self._AWAITING_SOURCE:
                self._source_selected(square)
            elif self._status == self._AWAITING_TARGET:
                self._target_selected(square)
            elif self._status == self._AWAITING_PROMOTION:
                self._promotion_selected(square)

        # not strictly necessary to draw and update every click
        # but it's an easy way to ensure necessary updates are always made
        self._update()
        self._draw()
        

    def _source_selected(self, square: chess.Square):
        if not square in self._position.from_squares:
            return
        self._source = square
        self._model.highlight = square
        self._status = self._AWAITING_TARGET 
        
    def _target_selected(self, square: chess.Square):
        self._target = square
        if self._source == self._target:
            self._source = None
            self._target = None
            self._model.highlight = None
            self._status = self._AWAITING_SOURCE            
        # we'lll handle promotion later
        # if self._is_promotion():
        #    self._draw_promotion_choices()
        #    self._status = self._AWAITING_PROMOTION
        else:
            move = chess.Move(self._source, self._target)
            if move in self._position.legal_moves:
                self._move_registered(move)
            else:
                self._model.highlight = None
                self._source = None
                self._target = None
                self._source_selected(square)

    def _move_registered(self, move: chess.Move):
        # TODO: parts of this should be factored out into methods
        # Moreover, the flow is perhaps backwards in places - as in, dealing
        # with the else branch before the if branch might make more sense.
        if move == self._position.move:
            # the move was correct
            self._present_solution()

            # I'm not keen on this - it feels like the scene shouldn't be flipping
            # the display - it should only be handling events and drawing views.
            #
            # Is this actually that wrong? And is there anyway around this?            
            pygame.display.flip()
            time.sleep(1)            

            # handle the position scheduling
            if self._failure == False:
                self._position.success()
            else:
                self._position.failure()

            # find out what to present next
            if self._trainer.is_complete:
                # update and save the completed chapter
                self._chapter.update_stats()
                self._chapter.write_to_disk()

                if self._chapters:
                    # start that next chapter                    
                    self._chapter = self._chapters.pop(0)
                    self._trainer = PositionTrainer(self._chapter)
                    self._position = self._trainer.pop()
                    self._present_problem()                    
                else:
                    # there are no chpaters left - the scene is done
                    self._display.pop_scene()
                    
            else:
                # the chapter isn't complete - so present the next problem
                self._position = self._trainer.pop()
                self._failure = False
                self._status = self._AWAITING_SOURCE
                self._present_problem()
                
        else:
            # the move was incorrect
            self._failure = True
            self._model.highlight = None
            self._status = self._AWAITING_SOURCE            
            self._update()
            self._draw()

    def _present_problem(self):
        self._failure = False
        self._setup_position(self._position.problem_board, self._position.perspective)
        self._update()
        self._draw()        

    def _present_solution(self):
        self._setup_position(self._position.solution_board, self._position.perspective)
        self._update()
        self._draw()        

    def _setup_position(self, board: chess.Board, perspective: chess.Color):
        self._model.perspective = perspective
        self._model.board = board
        self._model.highlight = None


class ZugTrainingView(ZugSceneView):
    def __init__(self, width, height):
        super().__init__(width, height)
        self._add_item('board', (100, 100), ZugBoardView())

    def update(self, model: ZugTrainingModel):
        self._items['board'].update(model)


class ZugTrainingModel(ZugSceneModel):
    def __init__(self):
        self._board = chess.Board()
        self._highlight = None
        self._perspective = chess.WHITE

    @property
    def perspective(self):
        return self._perspective

    @perspective.setter
    def perspective(self, perspective: chess.Color):
        self._perspective = perspective
        
    @property
    def board(self):
        return self._board

    @board.setter
    def board(self, board: chess.Board):
        self._board = board

    @property
    def highlight(self):
        return self._highlight

    @highlight.setter
    def highlight(self, square: chess.Square):
        self._highlight = square


    

_SQ_SIZE = 60

class ZugBoardView(ZugViewGroup):

    _WIDTH = _SQ_SIZE * 8
    _HEIGHT = _SQ_SIZE * 8

    _LABELS = [
        'a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1',
        'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8'
    ]

    def __init__(self):

        super().__init__()

        # generate an empty board from white's perspective
        # this should be refactored so that the squares don't move during the update,
        # the perspective shouldn't be relevant
        for square in chess.SQUARES:
            colour = chess.BLACK if ((square // 8) + square) % 2 == 0 else chess.WHITE
            square_name = chess.square_name(square)
            item_id = square_name
            label = square_name if square_name in self._LABELS else None
            position = self._coordinates(square, chess.WHITE)
            self._add_item(item_id, position, ZugSquareView(colour, label=label))

    def _coordinates(self, square: chess.Square, perspective: chess.Colour):
        if perspective == chess.WHITE:
            x = chess.square_file(square) * _SQ_SIZE
            y = (7 - chess.square_rank(square)) * _SQ_SIZE
        else:
            x = (7 - chess.square_file(square)) * _SQ_SIZE
            y = chess.square_rank(square) * _SQ_SIZE
        return (x, y)

    def update(self, model):
        # TODO: this is probably a bad design. The views shouldn't move, rather
        # the model should keep track of which chess square the view represents
        # assign positions to squares        
        # then unghighlight all squares and set the pieces
        board = model.board
        for square in chess.SQUARES:
            square_name = chess.square_name(square)
            self._items.pop(square_name)
            colour = chess.BLACK if ((square // 8) + square) % 2 == 0 else chess.WHITE
            square_name = chess.square_name(square)
            item_id = square_name
            label = square_name if square_name in self._LABELS else None
            position = self._coordinates(square, model.perspective)
            self._add_item(item_id, position, ZugSquareView(colour, label=label))
            self._items[square_name].set_piece(board.piece_at(square))
            self._items[square_name].unhighlight()
            self._items[square_name].move_unhighlight()            

        # set the move highlight
        if board.move_stack:
            move = board.peek()
            for square in (move.from_square, move.to_square):            
                vid = chess.square_name(square)
                self._items[vid].move_highlight()

        # set the square highlight
        square = model.highlight
        if square is not None:
            vid = chess.square_name(square)            
            self._items[vid].highlight()


class ZugSquareView(ZugView):

    _WIDTH = _SQ_SIZE
    _HEIGHT = _SQ_SIZE
    
    def __init__(
            self,
            colour: chess.Color,
            piece: Optional[chess.Piece]=None,
            label: Optional[str]=None
    ):
        super().__init__()
        self._colour = colour
        self._piece = piece
        self._label = label
        self._highlighted = False
        self._move_highlighted = False
        self._font = pygame.font.SysFont(None, 20)

    def set_highlight(self, highlighted: bool):
        self._highlighted = higlighted

    def highlight(self):
        self._highlighted = True

    def unhighlight(self):
        self._highlighted = False

    def set_move_highlight(self, highlighted: bool):
        self._move_highlighted = higlighted

    def move_highlight(self):
        self._move_highlighted = True

    def move_unhighlight(self):
        self._move_highlighted = False

    def set_piece(self, piece: Optional[chess.Piece]):
        self._piece = piece

    def draw(self):
        colour = self._background_colour()
        surface = pygame.Surface((self._WIDTH, self._HEIGHT))
        surface.fill(colour)
        if self._label is not None and not self._highlighted:
            label = self._font.render(self._label, True, self._label_colour())
            surface.blit(label, (60 - label.get_width() - 3, 2))
        if self._piece is not None:
            surface.blit(PIECE_IMAGES.get(self._piece), (0, 0))
        return surface

    def _background_colour(self):
        if self._highlighted:
            return THEME.white_highlight if self._colour == chess.WHITE \
                else THEME.black_highlight
        elif self._move_highlighted:
            return THEME.white_move_highlight if self._colour == chess.WHITE \
                else THEME.black_move_highlight
        else:
            return THEME.white if self._colour == chess.WHITE else THEME.black

    def _label_colour(self):
        return THEME.black if self._colour == chess.WHITE else THEME.white
