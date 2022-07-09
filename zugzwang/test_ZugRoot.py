import pytest
import mock
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
    ZugRoot,
    ZugColours,
    ZugDates,
)

TODAY = datetime.date(day=1, month=1, year=2000)
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)
PAST_EPOCH = TODAY - datetime.timedelta(days=1000)
FUTURE_EPOCH = TODAY + datetime.timedelta(days=1000)

NEW_REMAINING = 15
NEW_LIMIT = 20
REVIEW = 150
INACTIVE = 50

@pytest.fixture
def root_data():
    return ZugRootData(
        perspective = ZugColours.WHITE,
        last_access = TODAY,
        new_remaining = NEW_REMAINING,
        new_limit = NEW_LIMIT,
        review = REVIEW,
        inactive = INACTIVE,
    )

@pytest.fixture
def root_data_white_perspective(root_data):
    return root_data

@pytest.fixture
def root_data_black_perspective(root_data):
    root_data.perspective = ZugColours.BLACK
    return root_data

@pytest.fixture
def root(root_data):
    game = chess.pgn.Game()
    game.comment = root_data.make_comment()
    return ZugRoot(game)


def test_ZugRootData_from_comment():
    comment = (
        'perspective=WHITE;'
        'last_access=01-01-2000;'
        'new_remaining=15;'
        'new_limit=20;'
        'review=150;'        
        'inactive=50'
    )
    root_data = ZugRootData.from_comment(comment)
    assert root_data.last_access == TODAY
    assert root_data.new_remaining == NEW_REMAINING
    assert root_data.new_limit == NEW_LIMIT
    assert root_data.review == REVIEW
    assert root_data.inactive == INACTIVE


def test_ZugRootData_make_comment(root_data):
    expected_comment = (
        'perspective=WHITE;'
        'last_access=01-01-2000;'
        'new_remaining=15;'
        'new_limit=20;'
        'review=150;'
        'inactive=50'
    )
    assert root_data.make_comment() == expected_comment


class TestZugRootSolutionSet:

    @pytest.mark.parametrize(
        'pgn_filepath',
        ['TestPGNs/linear.pgn','TestPGNs/linear-hanging-problem.pgn']
    )
    def test_linear(
            self,
            root,
            pgn_filepath,
            root_data_black_perspective):
        # tests a PGN with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        with open(pgn_filepath) as pgn_file:
            game = chess.pgn.read_game(pgn_file)
            
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)

        node = game
        expected_solution_nodes = []
        for _ in range(5):
            node = node.variations[0]
            node = node.variations[0]
            expected_solution_nodes.append(node)

        assert root.solution_nodes() == expected_solution_nodes

    @pytest.mark.parametrize(
        'pgn_filepath',
        ['TestPGNs/branching.pgn','TestPGNs/branching-hanging-problems.pgn']
    )
    def test_branching(
            self,
            root,
            root_data_black_perspective,
            pgn_filepath
    ):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        with open(pgn_filepath) as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover three-move depth
        expected_solution_nodes = []    
        for problem in game.variations:
            for solution in problem.variations:
                expected_solution_nodes.append(solution)
                for problem in solution.variations:
                    for solution in problem.variations:
                        expected_solution_nodes.append(solution)

        root = ZugRoot(game)
        assert root.solution_nodes() == expected_solution_nodes

    def test_unreachable(self, root, root_data_black_perspective):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        with open('TestPGNs/unreachable.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover two-move depth, and searching only the first variation
        # of problems
        expected_solution_nodes = []
        for problem in game.variations:
            solution = problem.variations[0]
            expected_solution_nodes.append(solution)
            for problem in solution.variations:
                solution = problem.variations[0]
                expected_solution_nodes.append(solution)

        assert root.solution_nodes() == expected_solution_nodes

    def test_basic_blunder(self, root, root_data_black_perspective):
        # tests a PGN with single blunder
        with open('TestPGNs/blunder.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)

        # there are only two solution, so grab them explicity
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])
    
        assert root.solution_nodes() == expected_solution_nodes


    def test_blunders_and_branching(
            self,
            root,
            root_data_black_perspective
    ):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        with open('TestPGNs/blunders-and-branching.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]    
        expected_solution_nodes.append(solution)
        blunder = problem.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)

        problem = game.variations[1]    
        solution = problem.variations[0]    
        expected_solution_nodes.append(solution)
        blunder = problem.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)
        for problem in refutation.variations:
            expected_solution_nodes.append(problem.variations[0])
    
        assert root.solution_nodes() == expected_solution_nodes

    def test_hanging_blunders(
            self,
            root,
            root_data_black_perspective
    ):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        with open('TestPGNs/hanging-blunders.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)

        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]
        expected_solution_nodes.append(solution)
        problem = solution.variations[0]
        blunder = problem.variations[0]
        expected_solution_nodes.append(blunder.variations[0])    
    
        assert root.solution_nodes() == expected_solution_nodes

    def test_blunder_and_unreachable(
            self,
            root,
            root_data_black_perspective
    ):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        with open('TestPGNs/blunder-and-unreachable.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)    

        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])    

        assert root.solution_nodes() == expected_solution_nodes

    def test_double_blunders(
            self,
            root,
            root_data_black_perspective
    ):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        with open('TestPGNs/double-blunders.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_black_perspective.make_comment()
        root = ZugRoot(game)
    
        expected_solution_nodes = []
        expected_solution_nodes.append(game.variations[0])
        blunder = game.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)
        problem = refutation.variations[0]
        return_blunder = problem.variations[0]
        refutation = return_blunder.variations[0]            
        expected_solution_nodes.append(refutation)
        for problem in refutation.variations:
            expected_solution_nodes.append(problem.variations[0])

        assert root.solution_nodes() == expected_solution_nodes

    def test_white_from_starting_position(
        self,
        root,
        root_data_white_perspective
    ):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        with open('TestPGNs/white-from-starting-position.pgn') as pgn_file:
            game = chess.pgn.read_game(pgn_file)
        
        game.comment = root_data_white_perspective.make_comment()
        root = ZugRoot(game)

        expected_solution_nodes = []
        solution = game.variations[0]
        expected_solution_nodes.append(solution)
        for problem in solution.variations:
            expected_solution_nodes.append(problem.variations[0])

        assert root.solution_nodes() == expected_solution_nodes


class TestZugRootUpdateNewRemaining:
    

    @pytest.mark.parametrize(
        'last_access, expected_new_remaining',
        [
            (PAST_EPOCH, NEW_LIMIT),
            (YESTERDAY, NEW_LIMIT),
            (TODAY, NEW_REMAINING),
        ]
    )
    def test_all(self, root_data, last_access, expected_new_remaining):
        
        game = chess.pgn.Game()
        root_data.last_access = last_access
        game.comment = root_data.make_comment()
        ZugDates.today = mock.MagicMock(return_value = TODAY)        

        root = ZugRoot(game)

        root.update_new_remaining()
        assert root._data.new_remaining == expected_new_remaining


class TestZugRootTrainingNodes:
    pass

class TestZugRootUpdate:
    pass
    # The point should be that the status of the comments on all nodes
    # i.e. root and solution nodes is correct unless the last access date is before
    # today
    # we should have a method that determines whether the comments need updating
    # i.e. whether an update is due
    # cases: No updation - the last access date is today
    # no updation - the last access date is prior today but there are no 


class TestZugChapter:
    pass
