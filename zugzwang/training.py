from __future__ import annotations
from typing import List, Union

from zugzwang.queue import Queue
from zugzwang.game import ZugSolution

# TODO fix this: we need this for typing but it creates a circular import
#from zugzwang.chapter import ZugChapter

class TrainingStatuses:
    NEW = 'NEW'
    LEARNING_STAGE_1 = 'LEARNING_STAGE_1'
    LEARNING_STAGE_2 = 'LEARNING_STAGE_2'
    REMEMBERING_STAGE_1 = 'REMEMBERING_STAGE_1'
    REMEMBERING_STAGE_2 = 'REMEMBERING_STAGE_2'
    REVIEW = 'REVIEW'


class Position:
    def __init__(self, solution: ZugSolution, status: str=None):
        self._solution = solution
        self._status = status
        self._problem_board = solution.node.parent.board()
        self._solution_board = solution.node.board()        
        self._perspective = self._problem_board.turn

    @property
    def solution(self):
        return self._solution

    @property
    def status(self):
        return self._status

    @property
    def legal_moves(self):
        return self._problem_board.legal_moves

    @property
    def from_squares(self):
        return {move.from_square for move in self.legal_moves}

    @property
    def move(self):
        return self._solution.node.move

    @property
    def problem_board(self):
        return self._problem_board

    @property
    def solution_board(self):
        return self._solution_board

    @property
    def perspective(self):
        return self._perspective

    def success(self):
        return self._on_success()

    def failure(self):
        return self._on_failure()
            
    def _on_success(self):
        TS = TrainingStatuses
        statuses = {
            TS.NEW: TS.LEARNING_STAGE_1,
            TS.LEARNING_STAGE_1: TS.LEARNING_STAGE_2,
            TS.LEARNING_STAGE_2: TS.REVIEW,
            TS.REMEMBERING_STAGE_1: TS.REMEMBERING_STAGE_2,
            TS.REMEMBERING_STAGE_2: TS.REVIEW,
            TS.REVIEW: TS.REVIEW,             
        }
        actions = {
            TS.NEW: lambda: None,
            TS.LEARNING_STAGE_1: lambda: None,
            TS.LEARNING_STAGE_2: self._solution.learned,
            TS.REMEMBERING_STAGE_1: lambda: None,
            TS.REMEMBERING_STAGE_2: self._solution.remembered,
            TS.REVIEW: self._solution.recalled,  
        }
        directives = {
            TS.NEW: True,
            TS.LEARNING_STAGE_1: True,
            TS.LEARNING_STAGE_2: False, 
            TS.REMEMBERING_STAGE_1: True,
            TS.REMEMBERING_STAGE_2: False,
            TS.REVIEW: False, 
        }
        # The action and directive depend on the current status.
        # So perform the action and set the directive *before* updating the status.
        actions.get(self._status).__call__()
        directive = directives.get(self._status)
        self._status = statuses.get(self._status)
        return directive

    def _on_failure(self):
        TS = TrainingStatuses        
        statuses = {
            TS.NEW: TS.LEARNING_STAGE_1,                        
            TS.LEARNING_STAGE_1: TS.LEARNING_STAGE_1,
            TS.LEARNING_STAGE_2: TS.LEARNING_STAGE_1,
            TS.REMEMBERING_STAGE_1: TS.REMEMBERING_STAGE_1,
            TS.REMEMBERING_STAGE_2: TS.REMEMBERING_STAGE_1,
            TS.REVIEW: TS.REMEMBERING_STAGE_1,
        }
        directives = {
            TS.NEW: True,            
            TS.LEARNING_STAGE_1: True,
            TS.LEARNING_STAGE_2: True,
            TS.REMEMBERING_STAGE_1: True,
            TS.REMEMBERING_STAGE_2: True,
            TS.REVIEW: True,
        }
        actions = {
            TS.NEW: lambda: None,            
            TS.LEARNING_STAGE_1: lambda: None,
            TS.LEARNING_STAGE_2: lambda: None,
            TS.REMEMBERING_STAGE_1: lambda: None,
            TS.REMEMBERING_STAGE_2: lambda: None,
            TS.REVIEW: self._solution.forgotten,
        }
        # The action and directive depend on the current status.
        # So perform the action and set the directive *before* updating the status.
        actions.get(self._status).__call__()
        directive = directives.get(self._status)
        self._status = statuses.get(self._status)
        return directive


class Line:
    def __init__(self, line: List[chess.pgn.GameNode], root: ZugRoot):
        # the line is stored interanlly as a list of solutions
        self._line = [Position(ZugSolution(node, root)) for node in line[1::2]]
        self._perspective = line[0].board().turn

    def as_list(self):
        """Returns a shallow copy of the line."""
        return self._line[:]


class Trainer:

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    _INSERTION_INDEX = 3
    _INSERTION_RADIUS = 1

    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = Queue(self._INSERTION_INDEX, self._INSERTION_RADIUS)        
        self._fill_queue()
        self._position = None
    
    @property
    def is_complete(self):
        return self._queue.is_empty

    def report_result(self, result: str) -> Union[Position, None]:
        """Report that a training unit was completed, with a success status."""
        raise NotImplementedError

    def _fill_queue(self):
        raise NotImplementedError


class PositionTrainer(Trainer):

    _INSERTION_INDEX = 3
    _INSERTION_RADIUS = 1

    def start(self):
        if not self._queue.is_empty:
            self._position = self._queue.pop()
        return self._position
    
    def report_result(self, result: str) -> Union[Position, None]:
        
        if result == self.SUCCESS:
            reinsert = self._position.success()
        else:
            reinsert = self._position.failure()

        if reinsert:
            self._queue.insert(self._position)

        if self._queue.is_empty:
            self._position = None
        else:
            self._position = self._queue.pop()

        return self._position

    def _fill_queue(self):
        learning_capacity = self._chapter.root.data.learning_remaining
        for solution in self._chapter.solutions:
            if (not solution.is_learned()) and learning_capacity > 0:
                self._queue.append(Position(solution, TrainingStatuses.NEW))
                learning_capacity -= 1
                continue
            if solution.is_learned() and solution.is_due():
                self._queue.append(Position(solution, TrainingStatuses.REVIEW))
                continue


class LineTrainer(Trainer):

    def __init__(self, chapter: Chapter):
        super().__init__(chapter)
        self._line = None
        self._line_list = None

    def _fill_queue(self):
        for line in self._chapter.build_lines():
            self._queue.append(line)

    def start(self):
        if not self._queue.is_empty:
            self._line = self._queue.pop()
            self._line_list = self._line.as_list()
            self._position = self._line_list.pop(0)

        return self._position

    def report_result(self, result: str) -> Union[Position, None]:
        
        if result == self.SUCCESS:

            if self._line_list:
                # we're midway through a line, use the next position                
                self._position = self._line_list.pop(0)

            # we're at the end of a line
            elif self._queue.length != 0:
                # there's another line, so start that one                
                self._line = self._queue.pop()
                self._line_list = self._line.as_list()
                self._position = self._line_list.pop(0)

            else:
                # there are no more lines; the session is complete
                self._position = None

        elif result == self.FAILURE:
            
            # put the current line back into the queue
            self._queue.insert(self._line)
            self._line = self._queue.pop()
            self._line_list = self._line.as_list()
            self._position = self._line_list.pop(0)

        return self._position


