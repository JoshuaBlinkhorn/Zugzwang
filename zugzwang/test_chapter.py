import pytest
import os
import chess

from zugzwang.chapter import (
    ZugChapter,
    ZugStats,
)
from zugzwang.game import (
    ZugRootData,
    ZugSolutionData,
)
from zugzwang.constants import ZugSolutionStatuses, ZugColours

TEST_CATEGORY_PATH = os.path.join(
    os.getcwd(), "TestCollections/ExampleCollection/ChapterTestCHPs"
)

# TODO
# Figure out how to unit test this class.
# Is it sufficiently high-level that these tests can be considered automated
# integration tests? They will likely need to open and save files, and check their
# content. So we need to figure out how to make these processes backwards compatible,
# as the .chp standard format will certainly expand.


class TestZugChapter:
    def test_constructor_empty_chp(self):
        """Sanity checks for opening an empty chapter."""

        chp_filepath = os.path.join(TEST_CATEGORY_PATH, "empty.chp")
        chapter = ZugChapter(chp_filepath)

        expected_solutions = []
        expected_root_data = ZugRootData()
        expected_stats = ZugStats()

        assert chapter.solutions == expected_solutions
        assert chapter.root.data == expected_root_data
        assert chapter.stats == expected_stats

    def test_constructor_naked_chp(self):

        chp_filepath = os.path.join(TEST_CATEGORY_PATH, "naked.chp")
        chapter = ZugChapter(chp_filepath)

        expected_solution_data = ZugSolutionData()
        expected_root_data = ZugRootData()
        expected_stats = ZugStats(new=5, due=0, learned=0, total=5)

        assert len(chapter.solutions) == 5
        for solution in chapter.solutions:
            assert solution.data == expected_solution_data
        assert chapter.root.data == expected_root_data
        assert chapter.stats == expected_stats

    def test_constructor_incomplete_fields(self):

        chp_filepath = os.path.join(TEST_CATEGORY_PATH, "incomplete-fields.chp")
        chapter = ZugChapter(chp_filepath)

        expected_solution_data = ZugSolutionData(status=ZugSolutionStatuses.LEARNED)
        expected_root_data = ZugRootData(perspective=ZugColours.BLACK)
        expected_stats = ZugStats(new=0, due=5, learned=5, total=5)

        assert len(chapter.solutions) == 5
        for solution in chapter.solutions:
            assert solution.data == expected_solution_data
        assert chapter.root.data == expected_root_data
        assert chapter.stats == expected_stats

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
