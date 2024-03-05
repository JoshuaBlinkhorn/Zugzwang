import chess
import random
from typing import Optional, List
import abc
import enum

from zugzwang.gui import ZugGUI


# NOTE: QUIT is in these enums
# This deomonstrates that control of the session goes all the way down
# to the queue item.
# This is a feature of the current design in which the queue item talks
# to the GUI.
# That could be rearchitected - for the time being, it works.

class QueueItemResult(str, enum.Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    QUIT = 'QUIT'


class QueueDirective(str, enum.Enum):
    REINSERT = 'REINSERT'
    DISCARD = 'DISCARD'
    QUIT = 'QUIT'


class QueueItem(abc.ABC):
    def play(self, gui: ZugGUI) -> Optional[int]:
        return self._interpret_result(self._present(gui))

    @abc.abstractmethod
    def _present(self, gui: ZugGUI) -> QueueItemResult:
        pass

    def _on_success(self) -> QueueDirective:
        return QueueDirective.DISCARD

    def _on_failure(self) -> QueueDirective:
        return QueueDirective.REINSERT        

    def _interpret_result(
        self,
        result: QueueItemResult
    ) -> QueueDirective:
        if result == QueueItemResult.QUIT:
            return QueueDirective.QUIT        
        if result == QueueItemResult.SUCCESS:
            return self._on_success()
        if result == QueueItemResult.FAILURE:
            return self._on_failure()



class Queue():
    def __init__(
            self,
            insertion_index: int=0,
            insertion_radius: int=0,
    ):
        self._queue = []
        self._insertion_index = insertion_index
        self._insertion_radius = insertion_radius

    def _insert(
            self,
            item: QueueItem,
            index: Optional[int]=None,
            radius: Optional[int]=None,
    ):
        radius = radius if radius is not None else self._insertion_radius
        absolute_index = index if index is not None else self._insertion_index
        random_offset = random.randint(-radius, radius)        
        index = max(0, absolute_index+random_offset)
        self._queue.insert(index, item)

    def empty(self) -> None:
        self._queue = []
        
    def append(self, item: QueueItem) -> None:
        self._queue.append(item)

    def extend(self, items: List[QueueItem]) -> None:
        self._queue.extend(items)

    def play(self, gui: ZugGUI) -> None:
        while self._queue:
            item = self._queue.pop(0)
            directive = item.play(gui)
            if directive == QueueDirective.QUIT:
                break
            elif directive == QueueDirective.REINSERT:
                self._insert(item, self._insertion_index) 
            elif directive == QueueDirective.DISCARD:
                pass


