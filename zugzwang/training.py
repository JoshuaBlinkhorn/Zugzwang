from __future__ import annotations

from typing import Optional
import random
import dataclasses
from typing import List
import enum
import random
import abc

from zugzwang.cli_tools import clear_screen
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
    mode: TrainingMode = TrainingMode.LINES
    randomise: bool = True
    coalesce: bool = True


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
    tabias = list(item.tabias())
    if options.mode == TrainingMode.SCHEDULED:
        due_tabias = [tabia for tabia in tabias if tabia.is_due()]
        new_tabias = [tabia for tabia in tabias if not tabia.is_learned()]
        tabias = due_tabias + new_tabias[: config["learning_limit"]]
    return tabias


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

    def __init__(self, options: Optional[TrainingOptions] = None):
        self._options = options or TrainingOptions()
        self._queue = Queue(insertion_index=3, insertion_radius=1)

    def train(
        self,
        tabias: List[Tabia],
        gui: ZugGui,
        io_manager: IOManager,
    ) -> TrainingResult:
        if self._options.coalesce is True:
            return self._train_coalesced(tabias, gui)
        return _train(tabias, gui, io_manager)

    def _train_coalesced(self, tabias: List[Tabia], gui: ZugGui) -> None:
        self._queue.empty()
        self._fill_queue_coalesced(tabias)
        while not self._queue.is_empty():
            clear_screen()
            print(self._report_coalesced())
            self._queue.play_single(gui)

    def _train(
        self,
        tabias: List[Tabia],
        gui: ZugGui,
        io_manager: IOManager,
    ) -> TrainingResult:

        _ = io_manager
        self._queue.empty()
        result = TrainingResult.SUCCESS

        for tabia in tabias:
            self._fill_queue(tabia)
            while not self._queue.is_empty():
                clear_screen()
                print(self._report(tabia))
                if self._queue.play_single(gui) == QueueResult.FAILURE:
                    result = TrainingResult.FAILURE

        return result

    @abc.abstractmethod
    def _fill_queue(self, tabia: Tabia) -> None:
        pass

    @abc.abstractmethod
    def _fill_queue_coalesced(self, tabia: Tabia) -> None:
        pass

    def _report(self, tabia) -> str:
        name = tabia.name
        size = self._queue.size()
        return f"{tabia.name}: {size} remaining"

    def _report_coalesced(self) -> str:
        size = self._queue.size()
        return f"Coalesced: {size} remaining"


class LineTrainer(Trainer):
    def _fill_queue(self, tabia: Tabia) -> None:
        lines = [Line(line) for line in tabia.lines()]
        if self._options.randomise is True:
            random.shuffle(lines)
        self._queue.extend(lines)

    def _fill_queue_coalesced(self, tabias: List[Tabia]) -> None:
        lines = [Line(line) for tabia in tabias for line in tabia.lines()]
        if self._options.randomise is True:
            random.shuffle(lines)
        self._queue.extend(lines)


class ProblemTrainer(Trainer):
    def _fill_queue(self, tabia: Tabia) -> None:
        problems = [Problem(solution) for solution in tabia.solutions()]
        if self._options.randomise is True:
            random.shuffle(problems)
        self._queue.extend(problems)

    def _fill_queue_coalesced(self, tabias: List[Tabia]) -> None:
        problems = [
            Problem(solution) for tabia in tabias for solution in tabia.solutions()
        ]
        if self._options.randomise is True:
            random.shuffle(problems)
        self._queue.extend(problems)


class TabiaTrainer:
    def __init__(self, options: TrainingOptions):
        self._options = options
        self._queue = Queue(insertion_index=3, insertion_radius=1)

    def train(
        self,
        tabias: List[Tabia],
        gui: ZugGUI,
        io_manager: IOManager,
    ) -> None:

        if self._options.randomise:
            random.shuffle(tabias)

        for index, tabia in enumerate(tabias):
            result = TrainingResult.SUCCESS

            self._fill_queue_lines(tabia)
            while not self._queue.is_empty():
                clear_screen()
                print(self._report_lines(tabia, index + 1, len(tabias)))
                if self._queue.play_single(gui) == QueueResult.FAILURE:
                    result = TrainingResult.FAILURE

            self._fill_queue_problems(tabia)
            while not self._queue.is_empty():
                clear_screen()
                print(self._report_problems(tabia, index + 1, len(tabias)))
                if self._queue.play_single(gui) == QueueResult.FAILURE:
                    result = TrainingResult.FAILURE

            self._record_attempt(tabia, result)
            io_manager.write_meta(tabia)

    def _record_attempt(self, tabia: Tabia, result: TrainingResult) -> None:
        if result == TrainingResult.SUCCESS:
            tabia.record_attempt(TabiaResult.SUCCESS)
        elif result == TrainingResult.FAILURE:
            tabia.record_attempt(TabiaResult.FAILURE)

    def _fill_queue_lines(self, tabia: Tabia) -> None:
        lines = [Line(line) for line in tabia.lines()]
        if self._options.randomise is True:
            random.shuffle(lines)
        self._queue.extend(lines)

    def _fill_queue_problems(self, tabia: Tabia) -> None:
        problems = [Problem(solution) for solution in tabia.solutions()]
        if self._options.randomise is True:
            random.shuffle(problems)
        self._queue.extend(problems)

    def _report_lines(self, tabia: Tabia, index: int, total: int) -> None:
        name = tabia.name
        size = self._queue.size()
        return f"{tabia.name} ({index}/{total}): {size} lines remaining"

    def _report_problems(
        self,
        tabia: Tabia,
        index: int,
        total: int,
    ) -> None:
        name = tabia.name
        size = self._queue.size()
        return f"{tabia.name} ({index}/{total}): {size} problems remaining"


class TrainingSession(Scene):
    def __init__(self, spec: TrainingSpec, gui: ZugGUI):
        self._spec = spec
        self._gui = gui

    def go(self, io_manager: IOManager) -> Optional[SceneResult]:
        train(self._spec, self._gui, io_manager)
        return None

    def kill(self, io_manager: IOManager) -> None:
        pass
