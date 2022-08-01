# Python's workaround to annotate method's return type as enclosing class
from __future__ import annotations  

import chess.pgn
import datetime
import dataclasses
import json
from typing import List, ClassVar

from zugzwang.constants import ZugColours, ZugDefaults, ZugSolutionStatuses
from zugzwang.dates import ZugDates


class ZugRootError(ValueError):
    pass
    
class ZugDataError(Exception):
    pass
    

class ZugDefaults():
    LEARNING_REMAINING = 10
    LEARNING_LIMIT = 10
    RECALL_FACTOR = 2
    RECALL_RADIUS = 3
    RECALL_MAX = 365


class ZugData:

    def __init__(self):
        pass
            
    def __eq__(self, other: ZugData):
        return all([self.__dict__[key] == other.__dict__[key] for key in self.__dict__])

    @classmethod
    def _json_conversion(cls, value):
        # convert datetime.date to ISO date string
        if isinstance(value, datetime.date):
            return value.isoformat()
        raise TypeError('Cannot serialise python object in JSON.')

    @classmethod
    def from_json(cls, json_string: str) -> cls:
        # convert ISO date strings to datetime.date
        data_dict = json.loads(json_string)
        for key, val in data_dict.items():
            try:
                data_dict[key] = datetime.date.fromisoformat(val)
            except (TypeError, ValueError):
                pass
        return cls(**data_dict)

    def make_json(self) -> str:
        data_dict = dict(sorted(self.__dict__.items()))
        return json.dumps(data_dict, default = self._json_conversion)

    def update(self, update_dict) -> None:
        if not set(update_dict.keys()) <= set(self.__dict__.keys()):
            raise ZugDataError('attempted to update data dict with unrecognised key')
        self.__dict__.update(update_dict)
    

class ZugRootData(ZugData):
    def __init__(
            self,
            perspective: bool = ZugColours.WHITE,
            last_access: datetime.date = None,
            learning_remaining: int = ZugDefaults.LEARNING_REMAINING,
            learning_limit: int = ZugDefaults.LEARNING_LIMIT,
            recall_factor: float = ZugDefaults.RECALL_RADIUS,
            recall_radius: float = ZugDefaults.RECALL_FACTOR,
            recall_max: int = ZugDefaults.RECALL_MAX
    ):
        self.perspective = perspective
        self.last_access = ZugDates.today() if last_access is None else last_access
        self.learning_remaining = learning_remaining
        self.learning_limit = learning_limit
        self.recall_factor = recall_factor
        self.recall_radius = recall_radius
        self.recall_max = recall_max
        

class ZugSolutionData(ZugData):
    def __init__(
            self,
            status: str = ZugSolutionStatuses.UNLEARNED,
            last_study_date: datetime.date = None,
            due_date: datetime.date = None,
            successes: int = 0,
            failures: int = 0,
    ):
        self.status = status
        self.last_study_date = (
            ZugDates.yesterday() if last_study_date is None else last_study_date
        )
        self.due_date = ZugDates.yesterday() if due_date is None else due_date
        self.successes = successes
        self.failures = failures        


class ZugGameNodeWrapper:

    data_class = ZugData
    
    def __init__(self, game_node: chess.pgn.GameNode):
        self._game_node = game_node
        self._data = self.data_class.from_json(self._to_curly_braces(game_node.comment))
    
    @property
    def game_node(self):
        return self._game_node
        
    @property
    def data(self):
        return self._data
        
    @classmethod
    def _to_square_braces(cls, string):
        return string.replace('{','[').replace('}',']')
    
    @classmethod
    def _to_curly_braces(cls, string):
        return string.replace('[','{').replace(']','}')

    def _bind(self):
        self._game_node.comment = self._to_square_braces(self._data.make_json())


class ZugRoot(ZugGameNodeWrapper):

    data_class = ZugRootData

    def update(self) -> None:
        if self._data.last_access < ZugDates.today():
            self._data.learning_remaining = self._data.learning_limit
            self._data.last_access = ZugDates.today()
        self._bind()

    def decrement_learning_remaining(self) -> None:
        if self._data.learning_remaining == 0:
            error_message = "cannot decrement zero 'learning_remaining'"
            raise ZugRootError(error_message)
        self._data.learning_remaining -= 1
        self._bind()        

    def has_learning_capacity(self) -> bool:
        return self._data.learning_remaining > 0

    def solution_nodes(self) -> List[chess.pgn.ChildNode]:
        # define a list to store solutions and a recursive search function
        solutions = []
        def search_node(
                node: chess.pgn.GameNode,
                solution_perspective: bool
        ):
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution
                # add it to the set and work recursively on all children
                if node != self._game:
                    solutions.append(node)
                for problem in node.variations:
                    search_node(problem, solution_perspective)                
            else:
                # the node is a problem
                # if it has no variations, it's a hanging problem
                # otherwise, any variation is either a blunder or a candidate
                # find the first candidate if it exists, and work recursively
                candidates = [node for node in node.variations if 2 not in node.nags]
                if candidates:                    
                    search_node(candidates[0], solution_perspective)
                # work recursively on blunders with reversed perspective
                blunders = [node for node in node.variations if 2 in node.nags]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective)                    

        # call it on the root node
        solution_perspective = self._data.perspective                        
        search_node(self._game, solution_perspective)

        return solutions

    def lines(self) -> List[chess.Board]:

        # define an empty list to store the lines and a recursive search function        
        lines = []

        def is_blunder(node: chess.pgn_GameNode):
            return 2 in node.nags
                       
        def has_solution(problem: chess.pgn.GameNode):
            return any(not is_blunder(child) for child in problem.variations)
        
        def is_line_end(solution: chess.pgn.GameNode):
            # determining whether a given node is the end of a line is quite complex
            # to illustrate: a solution S may have a child problem P, such that P
            # has no child solution T, but it has a child blunder B
            # if P is the only child of S, then S is the end of the line
            #
            # the simplest characterisation is: the line ends at a solution unless
            # there exists a child problem with a child solution
            return not any(has_solution(problem) for problem in solution.variations)
        
        def search_node(
                node: chess.pgn.GameNode,
                solution_perspective: bool,
                prefix: List[chess.pgn.GameNode]
        ):
            # copy the prefix; necessary because otherwise all branches would modify
            # the same prefix 
            # it's easist to do this once, here at the top of the function
            prefix = prefix.copy()
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution
                # append it to the prefix if and only if it is not the root
                if node != self._game:
                    prefix.append(node)                
                # if the line ends here, add it to the set of lines
                # otherwise, work recursively on all children
                if is_line_end(node):
                    lines.append(prefix)
                for problem in node.variations:
                    search_node(problem, solution_perspective, prefix)
            else:
                # the node is a problem; append it to the prefix
                prefix.append(node)
                # if it has no variations, it's a hanging problem, ignore it
                # otherwise, any variation is either a candidate or a blunder
                # find the first candidate if it exists, and work recursively
                candidates = [node for node in node.variations if 2 not in node.nags]
                if candidates:
                    candidate = candidates[0]
                    search_node(candidate, solution_perspective, prefix)
                # work recursively on blunders with reversed perspective
                # and a new prefix starting at the blunder
                blunders = [node for node in node.variations if 2 in node.nags]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective, [])
        
        # call it on the root node
        solution_perspective = self._data.perspective                        
        search_node(self._game, solution_perspective, [])

        return lines


    # TODO: we should probably get all of these out of this class
    @classmethod
    def from_naked_game(cls, game: chess.pgn.Game, perspective: str):
        game.comment = ZugRootData(perspective=perspective).make_comment()
        root = ZugRoot(game)
        root._set_default_solution_data()
        return root
    
    def _set_default_solution_data(self):
        solution_data = ZugSolutionData()
        for solution in self.solution_nodes():
            solution.comment = solution_data.make_comment()                

    def reset_training_data(self):
        self._data = ZugRootData(perspective=self._data.perspective)
        self._game.comment = self._data.make_comment()
        self._reset_solution_data()


class ZugSolution():

    def __init__(self, node: chess.pgn.ChildNode, root: ZugRoot):
        self._data = ZugSolutionData.from_json(node.comment)
        self._node = node
        self._root = root

    @property
    def data(self):
        return self._data
        
    @property
    def node(self):
        return self._node
        
    @property
    def root(self):
        return self._root

    def is_learned(self):
        return self._data.status == ZugSolutionStatuses.LEARNED
        
    def is_due(self):
        return self.is_learned() and self._data.due_date <= ZugDates.today()
        
    def bind_data_to_comment(self):
        self._node.comment = self._data.make_json()

    def learned(self):
        self._root.decrement_learning_remaining()
        self._data.update(
            {
                'status': ZugSolutionStatuses.LEARNED,
                'last_study_date': ZugDates.today(),
                'due_date': ZugDates.tomorrow(),
                'successes': self._data.successes + 1,
            }
        )
        
    def recalled(self):
        next_due_date = ZugDates.due_date(
            self._data.last_study_date,
            self._data.due_date,
            self._root.data.recall_radius,
            self._root.data.recall_factor
        )
        self._data.update(
            {
                'successes': self._data.successes + 1,
                'last_study_date': ZugDates.today(),
                'due_date': next_due_date,
            }
        )
        
    def forgotten(self):
        self._data.update(
            {
                'status': ZugSolutionStatuses.UNLEARNED,                
                'failures': self._data.failures + 1,
            }
        )
