# Python's workaround to annotate method's return type as enclosing class
from __future__ import annotations  

import chess.pgn
import datetime
import dataclasses
import json
from typing import List, ClassVar

from zugzwang.constants import ZugColours, ZugSolutionStatuses
from zugzwang.dates import ZugDates


class ZugRootError(ValueError):
    pass
    
class ZugDataError(Exception):
    pass
    

class ZugDefaults():
    LEARNING_REMAINING = 10
    LEARNING_LIMIT = 10
    RECALL_FACTOR = 2.0
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
            recall_factor: float = ZugDefaults.RECALL_FACTOR,
            recall_radius: float = ZugDefaults.RECALL_RADIUS,
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
    """Abstract base class for wrapping chess nodes with custom functionality."""

    _data_class = ZugData
    
    def __init__(self, game_node: chess.pgn.GameNode):
        self._game_node = game_node
        self._data = self._data_class.from_json(self._to_curly_braces(game_node.comment))
    
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

    def bind(self):
        # Synchronise the node's comment with the wrapper's data
        self._game_node.comment = self._to_square_braces(self._data.make_json())


class ZugRoot(ZugGameNodeWrapper):

    _data_class = ZugRootData

    @property
    def recall_radius(self):
        return self._data.recall_radius
    
    @property
    def recall_factor(self):
        return self._data.recall_factor
    
    @property
    def recall_max(self):
        return self._data.recall_max
    
    def update(self) -> None:
        """
        Update the root's data.

        In particular, if the root was accessed last prior to today, update its
        learning_remaining and last_access.
        """
        if self._data.last_access < ZugDates.today():
            self._data.learning_remaining = self._data.learning_limit
            self._data.last_access = ZugDates.today()
        self.bind()

    def decrement_learning_remaining(self) -> None:
        """
        Decrement the learning_remaining, raising an exception if it is already
        non-positive.
        """
        if self._data.learning_remaining == 0:
            error_message = "cannot decrement zero 'learning_remaining'"
            raise ZugRootError(error_message)
        self._data.learning_remaining -= 1
        self.bind()        

    def has_learning_capacity(self) -> bool:
        return self._data.learning_remaining > 0

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


class ZugSolution(ZugGameNodeWrapper):

    _data_class = ZugSolutionData

    def __init__(self, solution, zug_root):
        super().__init__(solution)
        self._root = zug_root

    @property
    def data(self):
        return self._data
        
    @property
    def node(self):
        return self._game_node
        
    @property
    def root(self):
        return self._root

    def is_learned(self):
        return self._data.status == ZugSolutionStatuses.LEARNED
        
    def is_due(self):
        return self.is_learned() and self._data.due_date <= ZugDates.today()
        
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
        self.bind()        
        
    def recalled(self):
        next_due_date = ZugDates.due_date(
            self._data.last_study_date,
            self._data.due_date,
            self._root.recall_radius,
            self._root.recall_factor,
            self._root.recall_max,            
        )
        self._data.update(
            {
                'successes': self._data.successes + 1,
                'last_study_date': ZugDates.today(),
                'due_date': next_due_date,
            }
        )
        self.bind()
        
    def forgotten(self):
        self._data.update(
            {
                'status': ZugSolutionStatuses.UNLEARNED,                
                'failures': self._data.failures + 1,
            }
        )
        self.bind()

    def remembered(self):
        self._data.update(
            {
                'status': ZugSolutionStatuses.LEARNED,
                'last_study_date': ZugDates.today(),
                'due_date': ZugDates.tomorrow(),
                'successes': self._data.successes + 1,
            }
        )
        self.bind()
