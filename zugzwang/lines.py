import chess
import time
from typing import List

from zugzwang.queue import ZugQueueItem
from zugzwang.board import ZugBoard
from zugzwang.gui import ZugGUI


class ZugTrainingLine(ZugQueueItem):
    def __init__(self, line: List[chess.pgn.GameNode]):
        self._line = line

    def _present(self, gui: ZugGUI):
        return ZugTrainingLinePresenter(self._line).present(gui)


class ZugTrainingLinePresenter:
    def __init__(self, line: List[chess.pgn.GameNode], gui: ZugGUI):
        self._line = line
        self._gui = gui
        self._perspective = line[0].board().turn

    def present(self):
        self._gui.set_perspective(self._perspective)
        for problem, solution in zip(self._line[::2], self._line[1::2]):
            result = self._present_pair(problem, solution)
            if result != ZugQueueItem.SUCCESS:
                break
        return result

    def _present_pair(self, problem, solution):
        board = problem.board()
        self._gui.setup_position(board)
        gui_input = self._gui.get_input()

        if gui_input == ZugGUI.QUIT:
            return ZugQueueItem.QUIT
        elif type(gui_input) == chess.Move:
            move = gui_input
        else:
            raise ValueError("Input from ZugGUI not recognised.")

        if move == solution.move:
            self._gui.setup_position(solution.board())
            time.sleep(1)
            return ZugQueueItem.SUCCESS
        else:
            self._gui.setup_position(board)
            while self._gui.get_input() != solution.move:
                self._gui.setup_position(board)
            self._gui.setup_position(solution.board())
            time.sleep(1)
            return ZugQueueItem.FAILURE
