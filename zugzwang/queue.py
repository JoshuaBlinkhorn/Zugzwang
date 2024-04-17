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
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    QUIT = "QUIT"


class QueueItem(abc.ABC):
    @abc.abstractmethod
    def play(self, gui: ZugGUI) -> QueueResult:
        return self._present(gui)


class Queue:
    def __init__(
        self,
        insertion_index: int = 0,
        insertion_radius: int = 0,
    ):
        self._queue = []
        self._insertion_index = insertion_index
        self._insertion_radius = insertion_radius

    def _insert(
        self,
        item: QueueItem,
        index: Optional[int] = None,
        radius: Optional[int] = None,
    ):
        radius = radius if radius is not None else self._insertion_radius
        absolute_index = index if index is not None else self._insertion_index
        random_offset = random.randint(-radius, radius)
        index = max(0, absolute_index + random_offset)
        self._queue.insert(index, item)

    def empty(self) -> None:
        self._queue = []

    def append(self, item: QueueItem) -> None:
        self._queue.append(item)

    def extend(self, items: List[QueueItem]) -> None:
        self._queue.extend(items)

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)

    def play_single(self, gui: ZugGUI) -> None:
        item = self._queue.pop(0)
        result = item.play(gui)
        if result == QueueResult.QUIT:
            self.empty()
        if result == QueueResult.FAILURE:
            self.append(item)
        return result

    def play(self, gui: ZugGUI) -> QueueResult:
        queue_result = QueueResult.SUCCESS
        while self._queue:
            if self.play_single(gui) == QueueResult.FAILURE:
                queue_result = QueueResult.FAILURE

        return queue_result
