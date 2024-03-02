import time
from typing import List

import chess

from zugzwang.queue import QueueItem, QueueItemResult
from zugzwang.gui import ZugGUI

def _present_problem(solution: chess.pgn.ChildNode, gui: ZugGUI) -> QueueItemResult:
    failed = False    

    while (result := _get_result(solution, gui)) == QueueItemResult.FAILURE:
        failed = True
    if failed is True and result == QueueItemResult.SUCCESS:
        result = QueueItemResult.FAILURE

    return result


def _get_result(solution: chess.pgn.ChildNode, gui: ZugGUI) -> QueueItemResult:
    gui.setup_position(solution.parent.board())
    input_ = gui.get_input()

    if input_ == ZugGUI.QUIT:
        return QueueItemResult.QUIT
        
    if not isinstance(input_, chess.Move):
        raise ValueError('Input from ZugGUI not recognised.')

    if input_ == solution.move:
        gui.setup_position(solution.board())
        time.sleep(1)            
        return QueueItemResult.SUCCESS
    else:
        return QueueItemResult.FAILURE


class Problem(QueueItem):

    def __init__(self, solution: chess.pgn.ChildNode):
        self._solution = solution

    def _present(self, gui: ZugGUI) -> QueueItemResult:
        gui.set_perspective(self._solution.parent.board().turn)   
        return _present_problem(self._solution, gui)


class Line(QueueItem):
    def __init__(self, line: List[chess.pgn.GameNode]):
        self._line = line

    def _present(self, gui: ZugGUI):
        gui.set_perspective(self._line[0].board().turn)
        for solution in self._line[1::2]:
            if (result := _present_problem(solution, gui)) != QueueItemResult.SUCCESS:
                break
        return result
