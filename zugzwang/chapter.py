import chess
from typing import List

from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.training import ZugPositionTrainer, ZugLineTrainer
from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools

class ZugChapter():

    def __init__(self, chp_filepath: str):

        # parse filepath
        self._chp_filepath = chp_filepath                
        self.name = chp_filepath.split('/')[-1][:-4]
        self.category = chp_filepath.split('/')[-2]        
        self.collection = chp_filepath.split('/')[-3]
        
        # collect roots
        self._roots = []    
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)
            while game is not None:
                self._roots.append(ZugRoot(game))
                game = chess.pgn.read_game(chp_file)                
                
        # TODO deal with the perspective - it needs to be taken out of the chapter
        self._perspective = self._roots[0].data.perspective
        
        # form the solution set
        self._solutions = []
        for root in self._roots:
            nodes = ZugChessTools.get_solution_nodes(
                root.game_node,
                root.data.perspective
            )
            # solutions are linked to the 'primary root', which keeps the chapter's
            # metadata
            self._solutions.extend([ZugSolution(node, self._roots[0]) for node in nodes])

        # build the lines
        self._lines = []
        for root in self._roots:
            lines = ZugChessTools.get_lines(root.game_node, root.data.perspective)
            self._lines.extend(lines)

        # update the root and the stats
        self._update_root()
        self._update_stats()

    @property
    def root(self):
        return self._roots[0]
        
    @property
    def stats(self):
        return self._stats
        
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
        with open(self._chp_filepath, 'w') as chp_file:        
            for root in self._roots:
                print(root.game_node, file=chp_file, end='\n\n')

    def _update_root(self):
        self._roots[0].update()

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
        stats.new = min(stats.new, self._roots[0].data.learning_remaining)
        self._stats = stats

