import random
import dataclasses


from typing import List
import enum
import random

from zugzwang.group import Tabia
from zugzwang.queue import ZugQueue
from zugzwang.positions import ZugTrainingPosition, ZugTrainingStatuses
from zugzwang.lines import ZugTrainingLine
from zugzwang.gui import ZugGUI

# TODO fix this: we need this for typing but it creates a circular import
#from zugzwang.chapter import ZugChapter


class TrainingMode(str, enum.Enum):
    POSITIONS = "POSITIONS"
    LINES = "LINES"


@dataclasses.dataclass
class TrainingOptions:
    mode: TrainingMode=TrainingMode.LINES
    randomise: bool=True


class Trainer:

    def __init__(self, options=None):
        self._options = options or TrainingOptions()
        self._queue = ZugQueue()
        self._gui = ZugGUI()

    def _fill_queue(self, tabias: List[Tabia]):
        if self._options.mode == TrainingMode.POSITIONS:
            if self._options.randomise is True:
                random.shuffle(tabias)
            positions = [
                ZugTrainingPosition(solution, ZugTrainingStatuses.REVIEW, self._gui)
                for tabia in tabias
                for solution in tabia.solutions()
            ]
            for position in positions:
                self._queue.append(position)
            
        elif self._options.mode == TrainingMode.LINES:
            lines = [
                ZugTrainingLine(line, self._gui)
                for tabia in tabias
                for line in tabia.lines()
            ]
            if self._options.randomise is True:
                random.shuffle(lines)
            for line in lines:
                self._queue.append(line)

    def train(self, tabias: List[Tabia]):
        self._fill_queue(tabias)
        self._queue.play()
        self._gui.kill()


class ZugTrainer():
    
    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = ZugQueue()
        self._gui = ZugGUI()

    def _fill_queue(self):
        pass
        
    def train(self):
        self._fill_queue()
        self._queue.play()
        self._gui.kill()


class ZugPositionTrainer(ZugTrainer):
    
    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = ZugQueue(insertion_index=3, insertion_radius=1)
        self._gui = ZugGUI()

    def _fill_queue(self):
        learning_capacity = self._chapter.root.data.learning_remaining
        for solution in self._chapter.solutions():
            if (not solution.is_learned()) and learning_capacity > 0:
                self._queue.append(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.NEW, self._gui)
                )
                learning_capacity -= 1
                continue
            if solution.is_learned() and solution.is_due():
                self._queue.append(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.REVIEW, self._gui)
                )
                continue


