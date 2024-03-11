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

class QueueResult(str, enum.Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    QUIT = 'QUIT'


class QueueItem(abc.ABC):
    @abc.abstractmethod    
    def play(self, gui: ZugGUI) -> QueueResult:
        return self._present(gui)


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
        queue_result = QueueResult.SUCCESS
    
        while self._queue:
            item = self._queue.pop(0)
            result = item.play(gui)

            if result == QueueResult.QUIT:
                return result
            elif result == QueueResult.FAILURE:
                self._insert(item, self._insertion_index)
                queue_result = result

        return queue_result

