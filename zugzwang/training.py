from __future__ import annotations

from typing import Optional
import random
import dataclasses
from typing import List
import enum
import random
import abc

from zugzwang.group import Tabia
from zugzwang.queue import Queue
from zugzwang.problem import Problem, Line
from zugzwang.gui import ZugGUI


class TrainingMode(str, enum.Enum):
    TABIAS = "TABIA"
    PROBLEMS = "PROBLEMS"
    LINES = "LINES"


class TrainingStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"


class TrainingResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclasses.dataclass
class TrainingOptions:
    mode: TrainingMode=TrainingMode.LINES
    randomise: bool=True


def _get_trainer(options: TrainingOptions) -> Trainer:
    cls_dict = {
        TrainingMode.TABIAS: TabiaTrainer,
        TrainingMode.LINES: LineTrainer, 
        TrainingMode.PROBLEMS: ProblemTrainer,        
    }
    cls = cls_dict[options.mode]
    return cls(options)


def train(
        tabias: List[Tabias],
        options: TrainingOptions
) -> TrainingStatus:
    trainer = _get_trainer(options)
    gui = ZugGUI()

    trainer.train(tabias, gui)
    gui.kill()

    return TrainingStatus.COMPLETED


class Trainer(abc.ABC):

    def __init__(self, options: Optional[TrainingOptions]=None):
        self._options = options or TrainingOptions()
        self._queue = Queue(insertion_index=3, insertion_radius=1)

    def train(self, tabias: List[Tabia], gui: ZugGui):

        self._queue.empty()        
        self._fill_queue(tabias)
        self._queue.play(gui)

    @abc.abstractmethod
    def _fill_queue(self, tabias: List[Tabia]) -> None:
        pass
    

class LineTrainer(Trainer):
    def _fill_queue(self, tabias: List[Tabia]) -> None:
        lines = [Line(line) for tabia in tabias for line in tabia.lines()]
        if self._options.randomise is True:
            random.shuffle(lines)
        self._queue.extend(lines)


class ProblemTrainer(Trainer):
    def _fill_queue(self, tabias: List[Tabia]) -> None:    
        problems = [
            Problem(solution) for tabia in tabias for solution in tabia.solutions()
        ]
        if self._options.randomise is True:
            random.shuffle(problems)
        self._queue.extend(problems)
            

class TabiaTrainer(Trainer):
    def __init__(self, options: TrainingOptions):
        self._options = options
        self._line_trainer = LineTrainer(options)
        self._problem_trainer = ProblemTrainer(options)        


    def train(self, tabias: List[Tabia], gui: ZugGUI) -> None:
        if self._options.randomise:
            random.shuffle(tabias)
        for tabia in tabias:
            self._line_trainer.train([tabia], gui)
            self._problem_trainer.train([tabia], gui)
            

    def _fill_queue(self, tabias: List[Tabia]) -> None:
        pass

        
