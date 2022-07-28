import pytest
import mock
import datetime
import json
import chess.pgn
import os

from zugzwang.game import (
    ZugRootData,
    ZugRoot,
    ZugSolutionData,
    ZugSolution,
    LearningRemainingError,
)
from zugzwang.chapter import ZugChapter
from zugzwang.constants import ZugColours, ZugSolutionStatuses
from zugzwang.dates import ZugDates
from zugzwang.conftest import epoch_shift

# fix a mock epoch and dates relative to it
# fix root data values, different to defaults
# perhaps having these as constants is redundant now we have dataclasses implemtation
PERSPECTIVE = ZugColours.WHITE
LEARNING_REMAINING = 15
LEARNING_LIMIT = 20
RECALL_FACTOR = 2.5
RECALL_RADIUS = 5
RECALL_MAX = 500

# fix solution data
STATUS = ZugSolutionStatuses.LEARNED
LAST_STUDY_DATE = epoch_shift(-1)
DUE_DATE = epoch_shift(-1)
SUCCESSES = 5
FAILURES = 5

EXAMPLE_CATEGORY_PATH = os.path.join(
    os.getcwd(), 'TestCollections/ExampleCollection/ExampleCategory'
)

@pytest.fixture
def root_data_json():
    return (
        '{'
        '"perspective": true, '
        '"last_access": "2000-01-01", '
        '"learning_remaining": 15, '
        '"learning_limit": 20, '
        '"recall_factor": 2.5, '
        '"recall_radius": 5, '
        '"recall_max": 500'
        '}'
    )

@pytest.fixture
def solution_data_json():
    return (
        '{'
        '"status": "LEARNED", '
        '"last_study_date": "1999-12-31", '
        '"due_date": "1999-12-31", '
        '"successes": 5, '
        '"failures": 5'
        '}'
    )

@pytest.fixture
def root_data():
    return ZugRootData(
        perspective = ZugColours.WHITE,
        last_access = epoch_shift(0),
        learning_remaining = LEARNING_REMAINING,
        learning_limit = LEARNING_LIMIT,
        recall_factor = RECALL_FACTOR,
        recall_radius = RECALL_RADIUS,
        recall_max = RECALL_MAX,        
    )

@pytest.fixture
def root_data_white_perspective(root_data):
    return root_data

@pytest.fixture
def root_data_black_perspective(root_data):
    root_data.perspective = ZugColours.BLACK
    return root_data    

@pytest.fixture
def solution_data():
    return ZugSolutionData(
        status = ZugSolutionStatuses.LEARNED,
        last_study_date = epoch_shift(-1),
        due_date = epoch_shift(-1),
        successes = SUCCESSES,
        failures = FAILURES,
    )

@pytest.fixture
def root(root_data):
    game = chess.pgn.Game()
    game.comment = root_data.make_json()
    return ZugRoot(game)

@pytest.fixture
def solution(solution_data, root):
    node = chess.pgn.ChildNode(root.game, chess.Move.from_uci('e2e4'))
    node.comment = solution_data.make_json()
    return ZugSolution(node, root)

@pytest.fixture
def root_only_game():
    game = chess.pgn.Game()
    game.comment = ZugRootData().make_json()
    return game

@pytest.fixture
def simple_game():
    # a simple game - one root, one problem and one solution with default comments
    game = chess.pgn.Game()
    game.comment = ZugRoot().make_json()
    game.add_variation(chess.Move.from_uci('e2e4'))
    problem = game.variations[0]
    problem.add_variation(chess.Move.from_uci('e7e5'))
    solution = problem.variations[0]
    solution.comment = SolutionData.make_json()    
    return game

@pytest.fixture
def simple_root(simple_game):    
    return ZugRoot(simple_game)


class TestZugRootData:

    def test_from_json(self, root_data_json, root_data):
        assert ZugRootData.from_json(root_data_json) == root_data

    def test_make_json(self, root_data, root_data_json):
        assert root_data.make_json() == root_data_json


class TestZugSolutionData:

    def test_from_json(self, solution_data_json, solution_data):
        assert ZugSolutionData.from_json(solution_data_json) == solution_data

    def test_make_json(self, solution_data, solution_data_json):
        assert solution_data.make_json() == solution_data_json
    
    def test_update(self):
        pass


class TestZugRoot:
 
    def test_bind_data_to_comment(self):
        game = chess.pgn.Game()
        game.comment = ZugRootData().make_json()
        root = ZugRoot(game)

        root.data.perspective = ZugColours.BLACK
        root.data.last_access = epoch_shift(-1)        
        root.data.learning_remaining = 50
        root.data.learning_limit = 100
        root.data.recall_radius = 10
        root.data.recall_factor = 5.0
        root.data.recall_max = 500
        
        expected_json = (
            '{'
            '"perspective": false, '
            '"last_access": "1999-12-31", '
            '"learning_remaining": 50, '
            '"learning_limit": 100, '
            '"recall_factor": 5.0, '
            '"recall_radius": 10, '
            '"recall_max": 500'
            '}'
        )

        root.bind_data_to_comment()
        assert root.game.comment == expected_json

    @pytest.mark.parametrize(
        'last_access, expected_learning_remaining',
        [
            (epoch_shift(0), 15),
            (epoch_shift(-1), 20),
            (epoch_shift(-5), 20),
        ]
    )
    def test_update_learning_remaining(self, last_access, expected_learning_remaining):
        game = chess.pgn.Game()
        root_data = ZugRootData(
            learning_limit = 20,
            learning_remaining = 15,
            last_access=last_access
        )
        game.comment = root_data.make_json()
        root = ZugRoot(game)
        
        root.update_learning_remaining()
        assert root.data.learning_remaining == expected_learning_remaining
        
    def test_decrement_learning_remaining(self):
        game = chess.pgn.Game()
        root_data = ZugRootData(learning_remaining=2)
        game.comment = root_data.make_json()        
        root = ZugRoot(game)
        
        root.decrement_learning_remaining()
        assert root.data.learning_remaining == 1
        root.decrement_learning_remaining()
        assert root.data.learning_remaining == 0
        with pytest.raises(LearningRemainingError):
            root.decrement_learning_remaining()            

    @pytest.mark.parametrize(
        'learning_remaining, expected_has_learning_capacity',
        [(0, False), (1, True), (2, True), (100, True)]
    )
    def test_has_learning_capacity(
            self,
            learning_remaining,
            expected_has_learning_capacity
    ):
        game = chess.pgn.Game()
        root_data = ZugRootData(learning_remaining=learning_remaining)
        game.comment = root_data.make_json()
        root = ZugRoot(game)
        
        assert root.has_learning_capacity() == expected_has_learning_capacity

    # This should go into Chapter
    def redundant_test_from_naked_game(self):
        naked_game = chess.pgn.Game()
        naked_game.add_variation(chess.Move.from_uci('e2e4'))
        problem = naked_game.variations[0]
        problem.add_variation(chess.Move.from_uci('e7e5'))
        solution = problem.variations[0]
        
        root = ZugRoot.from_naked_game(naked_game)

        # the root and solution should have default comments
        assert naked_game.comment == ZugRootData().make_json()
        assert problem.comment == ZugSolutionData().make_json()        

    # This should go into Chapter
    def redundant_test_reset_training_data(self, root_data, solution_data):
        game = chess.pgn.Game()
        game.comment = root_data.make_json()
        game.add_variation(chess.Move.from_uci('e2e4'))
        problem = game.variations[0]
        problem.add_variation(chess.Move.from_uci('e7e5'))
        solution = problem.variations[0]
        solution.comment = solution_data.make_json()    

        root = ZugRoot(game)
        root.reset_training_data()
        
        # the root and solution should have default comments
        assert game.comment == ZugRootData().make_json()
        assert problem.comment == ZugSolutionData().make_json()        


class TestZugRootSolutionNodes():

    @pytest.mark.parametrize(
        'chp_filename', ['linear.chp', 'linear-hanging-problem.chp']
    )
    def test_linear(self, chp_filename):
        # tests a chapter with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        root = ZugChapter(chp_filepath).root
        game = root.game
        
        node = game
        expected_solution_nodes = []
        for _ in range(5):
            node = node.variations[0]
            node = node.variations[0]
            expected_solution_nodes.append(node)

        assert root.solution_nodes() == expected_solution_nodes

    @pytest.mark.parametrize(
        'chp_filename', ['branching.chp','branching-hanging-problems.chp']
    )
    def test_branching(self, chp_filename ):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        root = ZugChapter(chp_filepath).root
        game = root.game

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover three-move depth
        expected_solution_nodes = []    
        for problem in game.variations:
            for solution in problem.variations:
                expected_solution_nodes.append(solution)
                for problem in solution.variations:
                    for solution in problem.variations:
                        expected_solution_nodes.append(solution)

        assert root.solution_nodes() == expected_solution_nodes

    def test_unreachable(self):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

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

    def test_basic_blunder(self):
        # tests a PGN with single blunder
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there are only two solutions, so grab them explicity
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])
    
        assert root.solution_nodes() == expected_solution_nodes


    def test_blunders_and_branching(self):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunders-and-branching.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
    
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

    def test_hanging_blunders(self):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'hanging-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]
        expected_solution_nodes.append(solution)
        problem = solution.variations[0]
        blunder = problem.variations[0]
        expected_solution_nodes.append(blunder.variations[0])    
    
        assert root.solution_nodes() == expected_solution_nodes

    def test_blunder_and_unreachable(self):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder-and-unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
        
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])    

        assert root.solution_nodes() == expected_solution_nodes

    def test_double_blunders(self):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'double-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
        
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

    def test_white_from_starting_position(self):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        chp_filepath = os.path.join(
            EXAMPLE_CATEGORY_PATH,
            'white-from-starting-position.chp'
        )
        root = ZugChapter(chp_filepath).root
        game = root.game

        expected_solution_nodes = []
        solution = game.variations[0]
        expected_solution_nodes.append(solution)
        for problem in solution.variations:
            expected_solution_nodes.append(problem.variations[0])

        assert root.solution_nodes() == expected_solution_nodes


class TestZugRootLines():

    @pytest.mark.parametrize(
        'chp_filename',
        ['linear.chp','linear-hanging-problem.chp'],
    )
    def test_linear(self, chp_filename):
        # tests a PGN with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        root = ZugChapter(chp_filepath).root
        game = root.game

        line = list(game.mainline())[:10]
        expected_lines = [line]            

        assert root.lines() == expected_lines

    @pytest.mark.parametrize(
        'chp_filename',
        ['branching.chp','branching-hanging-problems.chp']
    )
    def test_branching(self, chp_filename):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        root = ZugChapter(chp_filepath).root
        game = root.game
        
        # there is no simpler way to do this than construct the lines manually.
        main = list(game.mainline())[0:4]
        line_a = main[:]
        variation = main[-3].variations[1]
        line_b = main[:-2] + [variation, variation.variations[0]]
        variation = game.variations[1]
        line_c = [variation] + list(variation.mainline())[:3]
        variation = line_c[-3].variations[1]
        line_d = line_c[:2] + [variation, variation.variations[0]]        
        expected_lines = [line_a, line_b, line_c, line_d]

        assert root.lines() == expected_lines
        
    def test_unreachable(self):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there is only one line, the main line
        expected_lines = [list(game.mainline())]

        assert root.lines() == expected_lines

    def test_basic_blunder(self):
        # tests a PGN with single blunder
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there two lines, the main line and the blunder line
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        expected_lines = [line_a, line_b]
        
        assert root.lines() == expected_lines

    def test_blunders_and_branching(self):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunders-and-branching.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # again, there is no clever way, we just build the lines
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        variation = game.variations[1]
        line_c = [variation, variation.variations[0]]
        blunder = variation.variations[1]
        line_d = [blunder] + list(blunder.mainline())
        variation = line_d[-3].variations[1]
        line_e = line_d[:2] + [variation, variation.variations[0]]
        expected_lines = [line_a, line_b, line_c, line_d, line_e]        
        
        assert root.lines() == expected_lines

    def test_hanging_blunders(self, root_data_black_perspective):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'hanging-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there are just two lines
        main = list(game.mainline())
        line_a = main[:2]
        line_b = main[-2:]
        expected_lines = [line_a, line_b]

        assert root.lines() == expected_lines

    def test_blunder_and_unreachable(self):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder-and-unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there two lines, the main line and the blunder line
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        expected_lines = [line_a, line_b]
        
        assert root.lines() == expected_lines        

    def test_double_blunders(self):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'double-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there are four lines
        line_a = [game, game.variations[0]]
        blunder = game.variations[1]
        line_b = [blunder, blunder.variations[0]]
        blunder = list(blunder.mainline())[2]
        line_c = [blunder] + list(blunder.mainline())
        variation = line_c[-3].variations[1]
        line_d = line_c[:2] + [variation, variation.variations[0]]
        expected_lines = [line_a, line_b, line_c, line_d]
        
        assert root.lines() == expected_lines

    def test_white_from_starting_position(self):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        chp_filepath = os.path.join(
            EXAMPLE_CATEGORY_PATH,
            'white-from-starting-position.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # here there are four lines, but we can exploit the structure or the PGN
        # with a for loop
        mainline = [game] + list(game.mainline())
        expected_lines = [mainline]
        junction = mainline[1]
        for variation in junction.variations[1:]:
            expected_lines.append(mainline[:2] + [variation, variation.variations[0]])

        assert root.lines() == expected_lines


class TestZugSolution():

    def test_bind_data_to_comment(self):
        game = chess.pgn.Game()
        game.comment = ZugRootData().make_json()
        root = ZugRoot(game)

        node = chess.pgn.ChildNode
        node.comment = ZugSolutionData().make_json()
        solution = ZugSolution(node, root)

        solution.data.status = ZugSolutionStatuses.LEARNED
        solution.data.last_study_date = epoch_shift(0)
        solution.data.due_date = epoch_shift(1)
        solution.data.successes = 10
        solution.data.failures = 10
        
        expected_json = (
            '{'
            '"status": "LEARNED", '
            '"last_study_date": "2000-01-01", '
            '"due_date": "2000-01-02", '
            '"successes": 10, '
            '"failures": 10'
            '}'
        )

        solution.bind_data_to_comment()
        assert solution.node.comment == expected_json

    def test_learned(self, solution):
        solution.learned()

        assert solution.root.data.learning_remaining == LEARNING_REMAINING - 1
        assert solution.data.status == ZugSolutionStatuses.LEARNED
        assert solution.data.last_study_date == epoch_shift(0)
        assert solution.data.due_date == epoch_shift(1)
        assert solution.data.successes == SUCCESSES + 1
        assert solution.data.failures == FAILURES                        

    def test_recalled(self, solution, monkeypatch):
        def mock_due_date(*args, **kwargs):
            return epoch_shift(10)
        monkeypatch.setattr(ZugDates, 'due_date', mock_due_date)
        
        solution.recalled()

        assert solution.root.data.learning_remaining == LEARNING_REMAINING
        assert solution.data.status == ZugSolutionStatuses.LEARNED
        assert solution.data.last_study_date == epoch_shift(0)
        assert solution.data.due_date == epoch_shift(10)
        assert solution.data.successes == SUCCESSES + 1
        assert solution.data.failures == FAILURES                        

    def test_forgotten(self, solution):
        solution.forgotten()

        assert solution.root.data.learning_remaining == LEARNING_REMAINING
        assert solution.data.status == ZugSolutionStatuses.UNLEARNED
        assert solution.data.last_study_date == LAST_STUDY_DATE
        assert solution.data.due_date == DUE_DATE
        assert solution.data.successes == SUCCESSES
        assert solution.data.failures == FAILURES + 1                      
    
