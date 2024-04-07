import time
from typing import List

import chess

from zugzwang.queue import QueueItem, QueueResult
from zugzwang.gui import ZugGUI


def _present_problem(solution: chess.pgn.ChildNode, gui: ZugGUI) -> QueueResult:
    failed = False

    while (result := _get_result(solution, gui)) == QueueResult.FAILURE:
        failed = True
    if failed is True and result == QueueResult.SUCCESS:
        result = QueueResult.FAILURE

    return result


def _get_result(solution: chess.pgn.ChildNode, gui: ZugGUI) -> QueueResult:
    gui.setup_position(solution.parent.board())
    input_ = gui.get_input()

    if input_ == ZugGUI.QUIT:
        return QueueResult.QUIT

    if not isinstance(input_, chess.Move):
        raise ValueError("Input from ZugGUI not recognised.")

    if input_ == solution.move:
        gui.setup_position(solution.board())
        time.sleep(1)
        return QueueResult.SUCCESS
    else:
        return QueueResult.FAILURE


class Problem(QueueItem):
    def __init__(self, solution: chess.pgn.ChildNode):
        self._solution = solution

    def play(self, gui: ZugGUI) -> QueueResult:
        gui.set_perspective(self._solution.parent.board().turn)
        return _present_problem(self._solution, gui)


class Line(QueueItem):
    def __init__(self, line: List[chess.pgn.GameNode]):
        self._line = line

    def play(self, gui: ZugGUI) -> QueueResult:
        result = QueueResult.SUCCESS
        gui.set_perspective(self._line[0].board().turn)
        for solution in self._line[1::2]:
            item_result = _present_problem(solution, gui)
            if item_result == QueueResult.QUIT:
                return QueueResult.QUIT
            if item_result == QueueResult.FAILURE:
                result = QueueResult.FAILURE
        return result
