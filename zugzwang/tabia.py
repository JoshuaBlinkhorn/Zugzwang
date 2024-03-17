import chess
from typing import List
from pathlib import Path

from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.training import ZugPositionTrainer, ZugLineTrainer
from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools


class Tabia:
    @property
    def name(self) -> str:
        return self._path.name

    @property
    def root(self) -> ZugRoot:
        return self._root

    @property
    def stats(self) -> ZugStats:
        return self._stats

    def solutions(self) -> List[ZugSolution]:
        return self._solutions

    def lines(self) -> List[List[chess.pgn.GameNode]]:
        return self._lines

    def train_positions(self):
        ZugPositionTrainer(self).train()
        self._root.update()
        self._save()
        self._generate_stats()

    def __init__(self, path: Path):
        # parse filepath
        self._path = path

        # collect root
        with open(path) as fp:
            game: chess.Game = chess.pgn.read_game(fp)
            self._root = ZugRoot(game)

        # form solution set
        nodes = ZugChessTools.get_solution_nodes(
            self._root.game_node, self._root.data.perspective
        )
        self._solutions = [ZugSolution(node, self.root) for node in nodes]

        # build lines
        self._lines = ZugChessTools.get_lines(
            self._root.game_node, self._root.data.perspective
        )

        # update root and stats
        self._root.update()
        self._generate_stats()

    def _save(self):
        with open(self._path, "w") as fp:
            print(self._root.game_node, file=fp)

    def _generate_stats(self):
        stats = ZugStats()
        for solution in self._solutions:
            if solution.is_learned():
                stats.learned += 1
            else:
                stats.new += 1
            if solution.is_due():
                stats.due += 1
            stats.total += 1
        stats.new = min(stats.new, self._root.data.learning_remaining)
        self._stats = stats
