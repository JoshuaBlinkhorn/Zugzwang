import pytest
import os

from zugzwang.chapter import ZugChapter

# TODO
# Figure out how to unit test this class.
# Is it sufficiently high-level that these tests can be considered automated
# integration tests? They will likely need to open and save files, and check their
# content. So we need to figure out how to make these processes backwards compatible,
# as the .chp standard format will certainly expand.

class TestZugChapter:

    def test_init(self):
        # The constructor is sufficiently complex that it requires a unit test.
        pass
    
    def test_update_stats(self):
        pass

    def test_save(self):
        pass


# These tests were considered redundant but they may be relevant to the Chapter class
    
class RedundantTests:

    # This should go into Chapter
    def redundant_test_from_naked_game(self):
        naked_game = chess.pgn.Game()
        naked_game.add_variation(chess.Move.from_uci("e2e4"))
        problem = naked_game.variations[0]
        problem.add_variation(chess.Move.from_uci("e7e5"))
        solution = problem.variations[0]

        root = ZugRoot.from_naked_game(naked_game)

        # the root and solution should have default comments
        assert naked_game.comment == ZugRootData().make_json()
        assert problem.comment == ZugSolutionData().make_json()

    # This should go into Chapter
    def redundant_test_reset_training_data(self, root_data, solution_data):
        game = chess.pgn.Game()
        game.comment = root_data.make_json()
        game.add_variation(chess.Move.from_uci("e2e4"))
        problem = game.variations[0]
        problem.add_variation(chess.Move.from_uci("e7e5"))
        solution = problem.variations[0]
        solution.comment = solution_data.make_json()

        root = ZugRoot(game)
        root.reset_training_data()

        # the root and solution should have default comments
        assert game.comment == ZugRootData().make_json()
        assert problem.comment == ZugSolutionData().make_json()

