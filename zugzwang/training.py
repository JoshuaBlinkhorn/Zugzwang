import random
import dataclasses

from zugzwang.queue import ZugQueue
from zugzwang.positions import ZugTrainingPosition, ZugTrainingStatuses
from zugzwang.lines import ZugTrainingLine
from zugzwang.gui import ZugGUI

# TODO fix this: we need this for typing but it creates a circular import
#from zugzwang.chapter import ZugChapter


class TrainingMode(str, enum.Enum):
    TABIAS = "TABIAS"
    LINES = "LINES"

@dataclasses.dataclass
class TrainingOptions:
    mode: TrainingMode=TrainingMode.LINES
    randomise: bool=True

class Trainer:

    def __init__(self, options=None):
        self._options = options or TrainingOptions()

    
    
    def train(units: List[Unit]) -> None:
        for unit in units:
            if isinstance(unit, Tabia):
                ZugPositionTrainer(unit).train()
                unit.save()
            elif isinstance(unit, Line):
                ZugLineTrainer()
    pass

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


class LineTrainer(ZugTrainer):

    def __init__(self, line: Line, gui: ZugGui):
        self._lines = lines
        self._queue = ZugQueue(insertion_index=3)
        self._gui = ZugGUI()        

    def _fill_queue(self):
        for line in self._get_lines():
            self._queue.append(line)

    def _get_lines(self):
        lines = [ZugTrainingLine(line, self._gui) for line in self._chapter.lines]
        random.shuffle(lines)
        return lines
