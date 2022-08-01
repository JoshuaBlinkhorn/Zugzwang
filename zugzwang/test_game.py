import pytest
import mock
import datetime
import json
import chess.pgn
import os

from zugzwang.game import (
    ZugData,
    ZugDataError,
    ZugRootData,
    ZugRoot,
    ZugRootError,    
    ZugSolutionData,
    ZugSolution,
)
from zugzwang.chapter import ZugChapter
from zugzwang.constants import ZugColours, ZugSolutionStatuses
from zugzwang.dates import ZugDates
from zugzwang.conftest import epoch_shift

# TODO (non-critical):
#
# 1. Generally clean up this file

# fix a mock today and dates relative to it
PAST_EPOCH = epoch_shift(-100)
YESTERDAY = epoch_shift(-1)
TODAY = epoch_shift(0)
TOMORROW = epoch_shift(1)
FUTURE_EPOCH = epoch_shift(100)

# fix default and alternative root data values
DEFAULT_PERSPECTIVE = ZugColours.WHITE
DEFAULT_LAST_ACCESS = TODAY
DEFAULT_LEARNING_REMAINING = 10
DEFAULT_LEARNING_LIMIT = 10
DEFAULT_RECALL_FACTOR = 2.0
DEFAULT_RECALL_RADIUS = 3
DEFAULT_RECALL_MAX = 365

ALTERNATE_PERSPECTIVE = ZugColours.BLACK
ALTERNATE_LAST_ACCESS = YESTERDAY
ALTERNATE_LEARNING_REMAINING = 100
ALTERNATE_LEARNING_LIMIT = 100
ALTERNATE_RECALL_FACTOR = 100.0
ALTERNATE_RECALL_RADIUS = 100
ALTERNATE_RECALL_MAX = 100

# fix default and alternative solution data values
#STATUS = ZugSolutionStatuses.LEARNED
#LAST_STUDY_DATE = YESTERDAY
#DUE_DATE = YESTERDAY
#SUCCESSES = 5
#FAILURES = 5

# define the path to the example category, which holds the example chapters
EXAMPLE_CATEGORY_PATH = os.path.join(
    os.getcwd(), 'TestCollections/ExampleCollection/ExampleCategory'
)

@pytest.fixture
def default_game_comment():
    return (
        '['
        '"last_access": "2000-01-01", '
        '"learning_limit": 20, '        
        '"learning_remaining": 15, '
        '"perspective": true, '        
        '"recall_factor": 2.5, '
        '"recall_max": 500, '
        '"recall_radius": 5'
        ']'
    )

@pytest.fixture
def alternate_game_comment():
    return (
        '['
        '"last_access": "1999-12-31", '
        '"learning_limit": 100, '
        '"learning_remaining": 100, '
        '"perspective": false, '
        '"recall_factor": 100.0, '
        '"recall_max": 100, '
        '"recall_radius": 100'
        ']'
    )

@pytest.fixture
def default_game_data():
    return ZugRootData(
        perspective = DEFAULT_PERSPECTIVE,
        last_access = DEFAULT_LAST_ACCESS,
        learning_remaining = DEFAULT_LEARNING_REMAINING,
        learning_limit = DEFAULT_LEARNING_LIMIT,
        recall_factor = DEFAULT_RECALL_FACTOR,
        recall_radius = DEFAULT_RECALL_RADIUS,
        recall_max = DEFAULT_RECALL_MAX,        
    )

@pytest.fixture
def alternate_game_data():
    return ZugRootData(
        perspective = ALTERNATE_PERSPECTIVE,
        last_access = ALTERNATE_LAST_ACCESS,
        learning_remaining = ALTERNATE_LEARNING_REMAINING,
        learning_limit = ALTERNATE_LEARNING_LIMIT,
        recall_factor = ALTERNATE_RECALL_FACTOR,
        recall_radius = ALTERNATE_RECALL_RADIUS,
        recall_max = ALTERNATE_RECALL_MAX,        
    )

@pytest.fixture
def solution_data_json():
    return (
        '['
        '"status": "LEARNED", '
        '"last_study_date": "1999-12-31", '
        '"due_date": "1999-12-31", '
        '"successes": 5, '
        '"failures": 5'
        ']'
    )

@pytest.fixture
def default_root_data_white_perspective(default_root_data):
    return root_data

@pytest.fixture
def default_data_black_perspective(default_root_data):
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


@pytest.fixture
def zug_data_subclass():
    # To test the class's functionality more thoroughly, we need to
    # create a subclass.
    class ZugDataSubclass(ZugData):
        def __init__(
                self,
                integer=0,
                floater=0.0,
                string='foobar',
                date=None,
        ):
            self.integer = integer
            self.floater = floater
            self.string = string
            self.date = date if date is not None else epoch_shift(0)

    return ZugDataSubclass


class TestZugData:

    def test_default(self):
        # The base class never has attributes.
        # So we test only against empty json.
        json = '{}'
        zug_data = ZugData()
        assert ZugData.from_json(json) == zug_data
        assert zug_data.make_json() == json        

    @pytest.mark.parametrize(
        'json, kwargs',
        [
            (
                (
                    '{'
                    '"date": "2000-01-01", '
                    '"floater": 0.0, '
                    '"integer": 0, '
                    '"string": "foobar"'
                    '}'
                ),
                {},
            ),
            (
                (
                    '{'
                    '"date": "2000-01-01", '
                    '"floater": 100.0, '
                    '"integer": 100, '
                    '"string": "barfoo"'
                    '}'
                ),
                {
                    'floater': 100.0,
                    'integer': 100,
                    'string': 'barfoo',
                },
            ),
            (
                (
                    '{'
                    '"date": "2000-01-02", '
                    '"floater": 0.0, '
                    '"integer": 0, '
                    '"string": "foobar"'
                    '}'
                ),
                {
                    'date': epoch_shift(1),
                },
            ),
        ],
        ids = [
            'empty',
            'non-default non-dates',
            'non-default date',
        ]
    )
    def test_json(self, zug_data_subclass, json, kwargs):
        # Translating to and from json works with a subset of parameters.
        zug_data = zug_data_subclass(**kwargs)
        assert zug_data_subclass.from_json(json) == zug_data
        assert zug_data.make_json() == json        

    @pytest.mark.parametrize(
        'update_dict, expected_dict',
        [
            (
                {},
                {
                    'date': epoch_shift(0),
                    'floater': 0.0,
                    'integer': 0,
                    'string': 'foobar',
                } 
            ),
            (
                {
                    'floater': 100.0,
                    'integer': 100,
                    'string': 'barfoo',                    
                },
                {
                    'date': epoch_shift(0),
                    'floater': 100.0,
                    'integer': 100,
                    'string': 'barfoo',
                } 
            ),
            (
                {
                    'date': epoch_shift(1),
                },
                {
                    'date': epoch_shift(1),
                    'floater': 0.0,
                    'integer': 0,
                    'string': 'foobar',
                } 
            ),
        ],
        ids = [
            'empty',
            'update non-dates',
            'update date',
        ]
    )
    def test_update(self, zug_data_subclass, update_dict, expected_dict):
        # Updating with recognised arguments updates the object __dict__.
        zug_data = zug_data_subclass()
        zug_data.update(update_dict)
        assert zug_data.__dict__ == expected_dict
        
    def test_update_foreign_attribute(self, zug_data_subclass):
        # Updating with unrecognised arguments raises an exception.       
        zug_data = zug_data_subclass()
        with pytest.raises(ZugDataError):
            zug_data.update({'unrecognised_key': 'any_value'})


class TestZugRootData:
    # This class overrides __init__() only.
    # Hence TestZugData() is sufficient to characterise its behaviour.
    pass


class TestZugSolutionData:
    # This class overrides __init__() only.
    # Hence TestZugData() is sufficient to characterise its behaviour.
    pass


class TestZugRoot:

    def test_bind(
            self,
            default_game_comment,
            alternate_game_comment
    ):
        game = chess.pgn.Game()
        game.comment = alternate_game_comment        
        zug_game = ZugRoot(game)
        
        game.comment = default_game_comment
        zug_game._bind()
        assert game.comment == alternate_game_comment

    @pytest.mark.parametrize(
        (
            'last_access, '
            'learning_remaining, '
            'expected_last_access, '
            'expected_learning_remaining'
        ),
        [
            (
                TODAY.isoformat(),
                DEFAULT_LEARNING_LIMIT - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_LIMIT - 1,
            ),
            (
                YESTERDAY.isoformat(),
                DEFAULT_LEARNING_LIMIT,
                TODAY.isoformat(),
                DEFAULT_LEARNING_LIMIT,
            ),
            (
                YESTERDAY.isoformat(),
                DEFAULT_LEARNING_LIMIT - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_LIMIT,
            ),
            (
                PAST_EPOCH.isoformat(),
                DEFAULT_LEARNING_LIMIT - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_LIMIT,
            ),
        ],
        ids = [
            'no update',
            'update identical learning_remaining',            
            'update last_access yesterday',
            'update last_access past_epoch',            
        ]
    )
    def test_update(
            self,
            default_game_comment,
            last_access,
            learning_remaining,
            expected_last_access,
            expected_learning_remaining,
    ):
        game = chess.pgn.Game()
        game.comment = (
            '['
            f'"last_access": "{last_access}", '
            '"learning_limit": 10, '            
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '            
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )        
        root = ZugRoot(game)
        
        root.update()
        assert game.comment == (
            '['
            f'"last_access": "{expected_last_access}", '
            '"learning_limit": 10, '            
            f'"learning_remaining": {expected_learning_remaining}, '
            '"perspective": true, '            
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )                    

    @pytest.mark.parametrize(
        'learning_remaining, expected_learning_remaining',
        [(1,0), (2,1), (10,9), (1000,999)],
        ids = ['smallest', 'small', 'medium', 'large']
    )
    def test_decrement_learning_remaining(
            self,
            learning_remaining,
            expected_learning_remaining
    ):
        game = chess.pgn.Game()
        game.comment = (
            '['
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '            
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )
        root = ZugRoot(game)
        
        root.decrement_learning_remaining()
        assert game.comment == (
            '['
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '            
            f'"learning_remaining": {expected_learning_remaining}, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )

    def test_decrement_zero_learning_remaining(self):
        # Decrementing a zero learning
        game = chess.pgn.Game()
        game.comment = (
            '['
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '            
            '"learning_remaining": 0, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )
        root = ZugRoot(game)
        with pytest.raises(ZugRootError):
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
        game.comment = (
            '['
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '            
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '            
            '"recall_factor": 2.0, '
            '"recall_max": 365, '            
            '"recall_radius": 3'
            ']'
        )
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
    
