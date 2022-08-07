import chess
from typing import List

from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.training import ZugPositionTrainer, ZugLineTrainer
from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools

class ZugChapter():

    def __init__(self, chp_filepath: str):
        # parse filepath
        self.name = chp_filepath.split('/')[-1][:-4]
        self.category = chp_filepath.split('/')[-2]        
        self.collection = chp_filepath.split('/')[-3]

        # build the root and solutions
        self._chp_filepath = chp_filepath        
        with open(chp_filepath) as chp_file:
            self._game = chess.pgn.read_game(chp_file)
        self._root = ZugRoot(self._game)
        self._perspective = self._root.data.perspective
        self._solutions = []  
        for solution_node in ZugChessTools.get_solution_nodes(
                self._game,
                self._perspective
        ):
            self._solutions.append(ZugSolution(solution_node, self._root))

        # build the lines
        self._lines = ZugChessTools.get_lines(self._game, self._perspective)

        # update the root and the stats
        self._update_root()                
        self._update_stats()

    @property
    def root(self):
        return self._root
        
    @property
    def solutions(self):
        return self._solutions

    @property
    def lines(self):
        return self._lines

    def train_positions(self):
        ZugPositionTrainer(self).train()
        self._update_root()
        self._save()        
        self._update_stats()

    def train_lines(self):
        ZugLineTrainer(self).train()
        self._update_root()
        self._save()        
        self._update_stats()

    def _save(self):
        print(self._game, file=open(self._chp_filepath, 'w'))

    def _update_root(self):
        self._root.update()

    def _update_stats(self):
        stats = ZugStats()
        for solution in self._solutions:
            if not solution.is_learned():
                stats.new += 1
            if solution.is_due():
                stats.due += 1
            if solution.is_learned():
                stats.learned += 1
            stats.total += 1
        stats.new = min(stats.new, self._root.data.learning_remaining)
        self.stats = stats

