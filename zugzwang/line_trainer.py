from typing import List
import chess
import random

from zugzwang.training import ZugTrainer
from zugzwang.queue import ZugQueue
from zugzwang.gui import ZugGUI
from zugzwang.lines import ZugTrainingLine


class LineTrainer(ZugTrainer):
    def __init__(self, lines: List[List[chess.pgn.GameNode]]):
        self._lines = lines
        self._queue = ZugQueue(insertion_index=3)
        self._gui = ZugGUI()

    def _fill_queue(self):
        lines = [ZugTrainingLine(line, self._gui) for line in self._lines]
        random.shuffle(lines)
        for line in lines:
            self._queue.append(line)
