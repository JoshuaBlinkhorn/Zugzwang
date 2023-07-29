import chess
import random
from typing import Optional, List, Any

from zugzwang.game import ZugSolution, ZugSolutionData
from zugzwang.board import ZugBoard
from zugzwang.gui import ZugGUI

class Queue():

    REINSERT = 'REINSERT'
    DISCARD = 'DISCARD'    

    def __init__(
            self,
            insertion_index: int=0,
            insertion_radius: int=0,
    ):
        self._queue = []
        self._insertion_index = insertion_index
        self._insertion_radius = insertion_radius

    @property
    def is_empty(self):
        return len(self._queue) == 0    

    @property
    def length(self):
        return len(self._queue)

    @property
    def items(self):
        return self._queue

    def insert(
            self,
            item: Any,
            index: Optional[int]=None,
            radius: Optional[int]=None,
    ) -> None:
        radius = radius if radius is not None else self._insertion_radius
        absolute_index = index if index is not None else self._insertion_index
        random_offset = random.randint(-radius, radius)
        index = max(0, absolute_index+random_offset)
        self._queue.insert(index, item)

    def append(self, item: Any):
        self._queue.append(item)

    def pop(self):
        return self._queue.pop(0)


# TODO (non-critical)
# 1. Decide whether to factor the _present_front() and _present_back() methods into
#    ZugQueueItem as they appear to be identical for both subclasses.
# 2. Decide whether the ZugTrainingPosition and ZugTrainingLine, and hence their
#    presenters too, belong with the training session classes, rather than the queue.
#    I think they probably do.

class ZugQueueItem():
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    QUIT = 'QUIT'

    def play(self) -> Optional[int]:
        return self._interpret_result(self._present())

    def _present(self) -> str:
        return self.SUCCESS

    def _interpret_result(self, result: str) -> Optional[int]:
        if result == self.QUIT:
            return ZugQueue.QUIT        
        if result == self.SUCCESS:
            return self._on_success()
        if result == self.FAILURE:
            return self._on_failure()

    def _on_success(self):
        return ZugQueue.DISCARD

    def _on_failure(self):
        return ZugQueue.REINSERT


class ZugQueue():

    REINSERT = 'REINSERT'
    DISCARD = 'DISCARD'
    QUIT = 'QUIT'

    def __init__(
            self,
            insertion_index: int=0,
            insertion_radius: int=0,
    ):
        self._queue = []
        self._insertion_index = insertion_index
        self._insertion_radius = insertion_radius

    def length(self):
        return len(self._queue)

    @property
    def items(self):
        return self._queue

    def insert(
            self,
            item: ZugQueueItem,
            index: Optional[int]=None,
            radius: Optional[int]=None,
    ):
        radius = radius if radius is not None else self._insertion_radius
        absolute_index = index if index is not None else self._insertion_index
        random_offset = random.randint(-radius, radius)        
        index = max(0, absolute_index+random_offset)
        self._queue.insert(index, item)

    def append(self, item: ZugQueueItem):
        self._queue.append(item)

    def pop(self):
        return self._queue.pop(0)

    def play(self) -> None:
        while self._queue:
            item = self._queue.pop(0)
            item_directive = item.play()
            if item_directive == self.QUIT:
                break
            if item_directive == self.REINSERT:
                self.insert(item, self._insertion_index)                
            if item_directive == self.DISCARD:
                pass


