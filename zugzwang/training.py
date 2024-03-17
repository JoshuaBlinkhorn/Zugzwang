from __future__ import annotations

from typing import Optional
import random
import dataclasses
from typing import List
import enum
import random
import abc

from zugzwang.config import config
from zugzwang.group import (
    Group,
    Item,
    Result as TabiaResult,    
    Tabia,
)
from zugzwang.queue import Queue, QueueResult
from zugzwang.problem import Problem, Line
from zugzwang.gui import ZugGUI
from zugzwang.scenes import Scene, SceneResult

# TODO: assess use of io_manager
# Having it pushed all the way into Trainer.train() feels wrong
# Training session return the trained tabias, and the caller saves those?


class TrainingMode(str, enum.Enum):
    TABIAS = "TABIA"
    SCHEDULED = "SCHEDULED"
    PROBLEMS = "PROBLEMS"
    LINES = "LINES"


class TrainingStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"


class TrainingResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INCOMPLETE = "INCOMPLETE"


@dataclasses.dataclass
class TrainingOptions:
    mode: TrainingMode=TrainingMode.LINES
    randomise: bool=True


@dataclasses.dataclass
class TrainingSpec:
    item: Item
    options: TrainingOptions


def _get_trainer(options: TrainingOptions) -> Trainer:
    cls_dict = {
        TrainingMode.TABIAS: TabiaTrainer,
        TrainingMode.SCHEDULED: TabiaTrainer,                
        TrainingMode.LINES: LineTrainer, 
        TrainingMode.PROBLEMS: ProblemTrainer,
    }
    cls = cls_dict[options.mode]
    return cls(options)

def _get_tabias(item: Item, options: TrainingOptions) -> List[Tabia]:
    if isinstance(item, Tabia):
        return [item]
    if options.mode == TrainingMode.SCHEDULED:
        due_tabias = [tabia for tabia in item.tabias() if tabia.is_due()]
        new_tabias = [tabia for tabia in item.tabias() if not tabia.is_learned()]
        tabias = due_tabias + new_tabias[:config['learning_limit']]
    return tabias


def train(
        tabias: List[Tabias],
        options: TrainingOptions,
        io_manager: IOManager,
) -> TrainingStatus:
    trainer = _get_trainer(options)
    gui = ZugGUI()

    trainer.train(tabias, gui)
    gui.kill()

    return TrainingStatus.COMPLETED


def train(
        spec: TrainingSpec,
        gui: ZugGUI,
        io_manager: IOManager,
) -> TrainingResult:
    trainer = _get_trainer(spec.options)
    tabias = _get_tabias(spec.item, spec.options)

    trainer.train(tabias, gui, io_manager)    

    return TrainingStatus.COMPLETED
    

class Trainer(abc.ABC):

    _result_map = {
        QueueResult.QUIT: TrainingResult.INCOMPLETE,
        QueueResult.SUCCESS: TrainingResult.SUCCESS,
        QueueResult.FAILURE: TrainingResult.FAILURE,        
    }
    
    def __init__(self, options: Optional[TrainingOptions]=None):
        self._options = options or TrainingOptions()
        self._queue = Queue(insertion_index=3, insertion_radius=1)

    def train(
            self,
            tabias: List[Tabia],
            gui: ZugGui,
            io_manager: IOManager,
            
    ) -> TrainingResult:
        _ = io_manager
        self._queue.empty()    
        self._fill_queue(tabias)
        return self._result_map[self._queue.play(gui)]

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


    def train(
            self,
            tabias: List[Tabia],
            gui: ZugGUI,
            io_manager: IOManager,
    ) -> TrainingResult:
        if self._options.randomise:
            random.shuffle(tabias)
        for tabia in tabias:
            res = TrainingResult.SUCCESS
            line_res = self._line_trainer.train([tabia], gui, io_manager)

            if line_res == QueueResult.QUIT:
                return TrainingResult.INCOMPLETE
            prob_res = self._problem_trainer.train([tabia], gui, io_manager)
            if prob_res == QueueResult.QUIT:
                return TrainingResult.INCOMPLETE
            if line_res == QueueResult.FAILURE or prob_res == QueueResult.FAILURE:
                res = TrainingResult.FAILURE

            self._record_attempt(tabia, res)
            io_manager.write_meta(tabia)

    def _record_attempt(self, tabia: Tabia, result: TrainingResult) -> None:
        if result == TrainingResult.SUCCESS:
            tabia.record_attempt(TabiaResult.SUCCESS)
        elif result == TrainingResult.FAILURE:
            tabia.record_attempt(TabiaResult.FAILURE)    

    def _fill_queue(self, tabias: List[Tabia]) -> None:
        pass

        
class TrainingSession(Scene):

    def __init__(self, spec: TrainingSpec, gui: ZugGUI):
        self._spec = spec
        self._gui = gui
    
    def go(self, io_manager: IOManager) -> Optional[SceneResult]:
        train(self._spec, self._gui, io_manager)
        return None

    def kill(self, io_manager: IOManager) -> None:
        pass
