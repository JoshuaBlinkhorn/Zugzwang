from typing import Optional
import random
import dataclasses


from typing import List
import enum
import random

from zugzwang.group import Tabia
from zugzwang.queue import Queue
from zugzwang.problem import Problem, Line
from zugzwang.gui import ZugGUI


class TrainingMode(str, enum.Enum):
    POSITIONS = "POSITIONS"
    LINES = "LINES"


@dataclasses.dataclass
class TrainingOptions:
    mode: TrainingMode=TrainingMode.LINES
    randomise: bool=True


class Trainer:

    def __init__(self, options: Optional[TrainingOptions]=None):
        self._options = options or TrainingOptions()
        self._queue = Queue(insertion_index=3, insertion_radius=1)

    def _fill_queue(self, tabias: List[Tabia]):
        if self._options.mode == TrainingMode.POSITIONS:
            if self._options.randomise is True:
                random.shuffle(tabias)
            problems = [
                Problem(solution)
                for tabia in tabias
                for solution in tabia.solutions()
            ]
            self._queue.extend(problems)
            
        elif self._options.mode == TrainingMode.LINES:
            lines = [
                Line(line)
                for tabia in tabias
                for line in tabia.lines()
            ]
            if self._options.randomise is True:
                random.shuffle(lines)
            self._queue.extend(lines)

    def train(self, tabias: List[Tabia]):
        gui = ZugGUI()
        self._fill_queue(tabias)
        self._queue.play(gui)
        gui.kill()


