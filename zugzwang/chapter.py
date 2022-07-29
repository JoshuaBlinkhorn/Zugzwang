import chess

from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.stats import ZugStats

class ZugChapter():

    @classmethod
    def _to_square_braces(cls, string):
        return string.replace('{','[').replace('}',']')
    
    @classmethod
    def _to_curly_braces(cls, string):
        return string.replace('[','{').replace(']','}')

    def _get_stats(self):
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
        return stats
    
    def __init__(self, chp_filepath: str):
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)
        game.comment = self._to_curly_braces(game.comment)
        self._chp_filepath = chp_filepath
        self._root = ZugRoot(game)
        self._root.update_learning_remaining()
        self._solutions = []        
        for solution_node in self._root.solution_nodes():
            solution_node.comment = self._to_curly_braces(solution_node.comment)
            self._solutions.append(ZugSolution(solution_node, self._root))
        self.stats = self._get_stats()
        self.name = chp_filepath.split('/')[-1][:-4]
        self.category = chp_filepath.split('/')[-2]        
        self.collection = chp_filepath.split('/')[-3]

    @property
    def root(self):
        return self._root
        
    @property
    def solutions(self):
        return self._solutions

    def save(self):
        self.stats = self._get_stats()
        self._root.update_learning_remaining()
        self._update_chp()

    def _update_chp(self):
        # prepare for writing
        self._root.bind_data_to_comment()
        self._root.game.comment = self._to_square_braces(self._root.game.comment)        
        for solution in self._solutions:
            solution.bind_data_to_comment()
            solution.node.comment = self._to_square_braces(solution.node.comment)

        # write
        print(self._root.game, file=open(self._chp_filepath, 'w'))

        # revert comments
        self._root.game.comment = self._to_curly_braces(self._root.game.comment)        
        for solution in self._solutions:
            solution.node.comment = self._to_curly_braces(solution.node.comment)


