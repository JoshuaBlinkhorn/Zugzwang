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
from zugzwang.training import Trainer, PositionTrainer, LineTrainer

class TrainingScene(ZugScene):

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
        self._failure_recorded = False
        self._source = None
        self._target = None
        self._status = self._AWAITING_SOURCE

        # start with the first chapter
        self._chapters = chapters
        self._chapter = self._chapters.pop(0)
        self._trainer = self._get_trainer()
        self._position = self._trainer.start()
        self._present_problem()

    def _get_trainer():
        raise NotImplementedError

    def _finish_chapter(self):
        pass

    def _present_problem(self):
        self._setup_position(self._position.problem_board, self._position.perspective)
        
        self._source = None
        self._target = None
        self._model.highlight = None
        self._failure_recorded = False        
        self._status = self._AWAITING_SOURCE
        
        self.refresh()

    def _present_solution(self):
        self._setup_position(self._position.solution_board, self._position.perspective)
        self.refresh()

    def _setup_position(self, board: chess.Board, perspective: chess.Color):
        self._model.perspective = perspective
        self._model.board = board
        self._model.highlight = None

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

    def _source_selected(self, square: chess.Square):
        """
        Highlight the selected source square if it's a source of a legal move.
        """
        if not square in self._position.from_squares:
            # this mightn't be necessary, but there no harm in doing it
            self._source = None
            self._target = None
            self._model.highlight = None
            self._status = self._AWAITING_SOURCE

        else:
            # it was a valid source selection
            self._source = square
            self._model.highlight = square
            self._status = self._AWAITING_TARGET
            self.refresh()
        
    def _target_selected(self, square: chess.Square):
        """
        Figure out whether the target is meaningful, and act accordingly.
        """
        self._target = square
        if self._source == self._target:
            # the source was deselected
            self._source = None
            self._target = None
            self._model.highlight = None
            self._status = self._AWAITING_SOURCE
            self.refresh()
    
        elif self._legal_promotion():
            # display the promotion choices and wait for selection
            self._view.promotion_inset()
            self.refresh()
            self._status = self._AWAITING_PROMOTION
        
        elif self._legal_non_promotion():
            # legal move registered
            self._move_registered(chess.Move(self._source, self._target))

        else:
            # the selected square doesn't create a legal move;
            # so unhiglight the source..
            self._source = None
            self._target = None
            self._model.highlight = None
            self.refresh()
            
            # .. and consider it a source selection            
            self._status = self._AWAITING_SOURCE
            self._source_selected(square)

    def _promotion_selected(self, square: chess.Square):
        """
        Detmerine whether the clicked square is a promotion choice, and act accordingly.
        """
        promotion_dict = self._promotion_dict()
        promotion = promotion_dict.get(square)
        if promotion == None:
            # the user backed out of selecting a promotion piece;
            # just reset the problem
            self._reset()
            self.refresh()
        else:
            # A promotion piece was selected, which is always a legal move;
            # despatch it
            self._move_registered(chess.Move(self._source, self._target, promotion))

    def _promotion_dict(self):
        """
        Generate a dictionary mappng promotion squares to promotion pieces
        """
        file = chess.square_file(self._target)
        ranks = (7, 6, 5, 4) if self._board.turn == chess.WHITE else (0, 1, 2, 3)
        pieces = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)
        return {chess.square(file, rank): piece for (rank, piece) in zip(ranks, pieces)}

    def _legal_promotion(self) -> bool:
        """
        Check whether promotion to a queen is a legal move; and hence whether the move,
        as currently determined by source and target, requires a promotion piece.
        """
        move = chess.Move(self._source, self._target, chess.QUEEN)
        return move in self._position.legal_moves                
        
    def _legal_non_promotion(self) -> bool:
        """
        Check whether the move, as currently determined by source and target, is legal.
        """
        move = chess.Move(self._source, self._target)
        return move in self._position.legal_moves

    def _move_registered(self, move: chess.Move):
        if move != self._position.move:
            # it's the wrong move; set the failure flag
            # TODO - we could put the move on the board and the immediately
            # put it back, to let the user knows it was registered
            self._failure_recorded = True
            self._model.highlight = None
            self._status = self._AWAITING_SOURCE
            self.refresh()            
            return

        # it's the correct move
        self._present_solution()
        
        # I'm not keen on this - it feels like the scene shouldn't be flipping
        # the display - it should only be handling events and drawing views.
        #
        # Is this actually that wrong? And is there anyway around this?            
        pygame.display.flip()
        time.sleep(1)            

        result = Trainer.FAILURE if self._failure_recorded else Trainer.SUCCESS
        next_position = self._trainer.report_result(result)
        
        if next_position is not None:
            # the chapter isn't complete - so present the next problem
            self._position = next_position
            self._present_problem()
            return

        # the chapter is complete
        self._finish_chapter()

        if not self._chapters:
            # there are no more chatpers to train - the scene is done
            self._display.pop_scene()
            return

        # there is at least one more chapter to train
        self._chapter = self._chapters.pop(0)
        self._trainer = self._get_trainer(self._chapter)
        self._position = self._trainer.start()
        self._present_problem()


class PositionTrainingScene(TrainingScene):
    def _get_trainer(self):
        return PositionTrainer(self._chapter)

    def _finish_chapter(self):
        self._chapter.update_stats()
        self._chapter.write_to_disk()


class LineTrainingScene(TrainingScene):
    def _get_trainer(self):
        return LineTrainer(self._chapter)


class ZugTrainingView(ZugSceneView):
    def __init__(self, width, height):
        super().__init__(width, height)
        self._add_item('board', (100, 100), ZugBoardView())

    def promotion_choices(self):
        pass

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
        if self._piece is not None:
            surface.blit(PIECE_IMAGES.get(self._piece), (0, 0))
        if self._label is not None and not self._highlighted:
            label = self._font.render(self._label, True, self._label_colour())
            surface.blit(label, (60 - label.get_width() - 3, 2))            
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
