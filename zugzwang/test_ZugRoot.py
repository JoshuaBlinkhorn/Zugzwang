import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
    ZugRoot,
    ZugColours,
)

TODAY = datetime.date(day=1, month=1, year=2000)
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)
PAST_EPOCH = TODAY - datetime.timedelta(days=1000)
FUTURE_EPOCH = TODAY + datetime.timedelta(days=1000)

@pytest.fixture
def root_data():
    return ZugRootData(
        perspective = ZugColours.WHITE,
        last_access = TODAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )

@pytest.fixture
def root(root_data):
    game = chess.pgn.Game()
    game.comment = root_data.make_comment()
    return ZugRoot(game)


def test_ZugRootData_from_comment():
    comment = (
        'perspective=WHITE;'
        'last_access=01-01-2000;'
        'new_remaining=20;'
        'new_limit=50;'
        'review=150;'        
        'inactive=50'
    )
    root_data = ZugRootData.from_comment(comment)
    assert root_data.last_access == TODAY
    assert root_data.new_remaining == 20
    assert root_data.new_limit == 50
    assert root_data.review == 150
    assert root_data.inactive == 50


def test_ZugRootData_make_comment(root_data):
    expected_comment = (
        'perspective=WHITE;'
        'last_access=01-01-2000;'
        'new_remaining=20;'
        'new_limit=50;'
        'review=150;'
        'inactive=50'
    )
    assert root_data.make_comment() == expected_comment


def test_ZugRoot_update_game_comment(root):
    root.update_game_comment


def test_update_status_counts(root):
    root.update_status_counts()

    
def test_reset_data(root):
    root.reset_data()

@pytest.mark.parametrize(
    'pgn_filepath',
    ['TestPGNs/linear.pgn','TestPGNs/linear-hanging-problem.pgn']
)
def test_ZugRoot_solution_set_linear(root, pgn_filepath):
    # tests a PGN with no branching and five solutions, ending with or without
    # a 'hanging problem'; i.e. a problem that is not followed by a solution
    with open(pgn_filepath) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    node = game

    expected_solution_nodes = []
    for _ in range(5):
        node = node.variations[0]
        node = node.variations[0]
        expected_solution_nodes.append(node)

    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


@pytest.mark.parametrize(
    'pgn_filepath',
    ['TestPGNs/branching.pgn','TestPGNs/branching-hanging-problems.pgn']
)
def test_ZugRoot_solution_set_branching(root, pgn_filepath):
    # tests a PGN with branching, three moves deep and no unreachable solutions
    with open(pgn_filepath) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()

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


def test_ZugRoot_solution_set_unreachable(root):
    # tests a PGN with unreachable solutions
    # for throroughness, the PGN also has branching and hanging problems
    with open('TestPGNs/unreachable.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()

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

    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_basic_blunder(root):
    # tests a PGN with single blunder
    with open('TestPGNs/blunder.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()

    # there are only two solution, so grab them explicity
    expected_solution_nodes = []
    problem = game.variations[0]
    expected_solution_nodes.append(problem.variations[0])
    blunder = problem.variations[1]
    expected_solution_nodes.append(blunder.variations[0])
    
    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_blunders_and_branching(root):
    # tests a PGN with branching and single blunders, i.e. the opponent does not
    # blunder back in the refutation
    with open('TestPGNs/blunders-and-branching.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    
    # the solution set with blunders is harder to compute due to the reverse in
    # perspective
    # the best way to get the solution nodes here is to grab them explicity
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
    
    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_hanging_blunders(root):
    # tests a PGN with hanging blunders, i.e. the blunder has no refutation
    # we also test blunders which aren't qualified by a proper solution
    # the distinction is important; a blunder is a problem, but it is also
    # an error; solutions to both exist, but their perspectives are different
    with open('TestPGNs/hanging-blunders.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    
    # the solution set with blunders is harder to compute due to the reverse in
    # perspective
    # the best way to get the solution nodes here is to grab them explicity
    expected_solution_nodes = []
    problem = game.variations[0]
    solution = problem.variations[0]
    expected_solution_nodes.append(solution)
    problem = solution.variations[0]
    blunder = problem.variations[0]
    expected_solution_nodes.append(blunder.variations[0])    
    
    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_blunder_and_unreachable(root):
    # tests a PGN with a node that has a solution, a blunder and an unreachable candidate
    with open('TestPGNs/blunder-and-unreachable.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    
    # the solution set with blunders is harder to compute due to the reverse in
    # perspective
    # the best way to get the solution nodes here is to grab them explicity
    expected_solution_nodes = []
    problem = game.variations[0]
    expected_solution_nodes.append(problem.variations[0])
    blunder = problem.variations[1]
    expected_solution_nodes.append(blunder.variations[0])    
    
    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_double_blunders(root):
    # tests a PGN in which the opponent blunders back in the refutation
    # hence the perspective will reverse twice in one line
    with open('TestPGNs/double-blunders.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.BLACK,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    
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
    
    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


def test_ZugRoot_solution_set_white_from_starting_position(root):
    # tests a PGN in which the training player has the move in the root position.
    # the other case is tested implicitly in several tests above
    with open('TestPGNs/white-from-starting-position.pgn') as pgn_file:
        game = chess.pgn.read_game(pgn_file)
        
    root_data =  ZugRootData(
        perspective = ZugColours.WHITE,
        last_access = YESTERDAY,
        new_remaining = 20,
        new_limit = 50,
        review = 150,
        inactive = 50,
    )
    game.comment = root_data.make_comment()
    
    expected_solution_nodes = []
    solution = game.variations[0]
    expected_solution_nodes.append(solution)
    for problem in solution.variations:
        expected_solution_nodes.append(problem.variations[0])    

    root = ZugRoot(game)
    assert root.solution_nodes() == expected_solution_nodes


