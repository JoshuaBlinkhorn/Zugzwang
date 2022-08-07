import chess
from typing import Optional, List

from zugzwang.game import ZugSolution, ZugSolutionData
from zugzwang.board import ZugBoard

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

    _REINSERTION_INDEX = 3
    
    def __init__(self):
        self._queue = []

    @property
    def queue(self):
        return self._queue

    def insert(
            self,
            item: ZugQueueItem,
            index: Optional[int]=None
    ):
        if index is not None:
            self._queue.insert(index, item)
        else:
            self._queue.append(item)

    def play(self) -> None:
        while self._queue:
            item = self._queue.pop(0)
            item_directive = item.play()
            if item_directive == self.QUIT:
                break
            if item_directive == self.REINSERT:
                self.insert(item, self._REINSERTION_INDEX)                
            if item_directive == self.DISCARD:
                pass


