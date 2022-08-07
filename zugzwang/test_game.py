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

# fix default solution data values
DEFAULT_STATUS = ZugSolutionStatuses.UNLEARNED
DEFAULT_LAST_STUDY_DATE = YESTERDAY
DEFAULT_DUE_DATE = YESTERDAY
DEFAULT_SUCCESSES = 0
DEFAULT_FAILURES = 0

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

DEFAULT_ROOT_COMMENT = (
        '['
        '"last_access": "2000-01-01", '
        '"learning_limit": 10, '        
        '"learning_remaining": 10, '
        '"perspective": true, '        
        '"recall_factor": 3.0, '
        '"recall_max": 365, '
        '"recall_radius": 3'
        ']'
)

ALTERNATE_ROOT_COMMENT = (
        '['
        '"last_access": "1999-12-31", '
        '"learning_limit": 100, '        
        '"learning_remaining": 100, '
        '"perspective": false, '        
        '"recall_factor": 100.0, '
        '"recall_max": 1000, '
        '"recall_radius": 100'
        ']'
)

DEFAULT_SOLUTION_COMMENT = (
        '['
        '"status": "LEARNED", '
        '"last_study_date": "1999-12-31", '
        '"due_date": "1999-12-31", '
        '"successes": 0, '
        '"failures": 0'
        ']'
)

@pytest.fixture
def default_solution_data():
    return ZugSolutionData(
        status = DEFAULT_STATUS,
        last_study_date = DEFAULT_LAST_STUDY_DATE,
        due_date = DEFAULT_DUE_DATE,
        successes = DEFAULT_SUCCESSES,
        failures = DEFAULT_FAILURES,
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
def default_root_data():
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
def default_root_data_white_perspective(default_root_data):
    return default_root_data

@pytest.fixture
def default_data_black_perspective(default_root_data):
    default_root_data.perspective = ZugColours.BLACK
    return default_root_data

@pytest.fixture
def game():
    game = chess.pgn.Game()
    game.comment = DEFAULT_ROOT_COMMENT
    return game

@pytest.fixture
def solution(game):
    solution = game.add_variation(chess.Move.from_uci('e2e4'))
    solution.comment = DEFAULT_SOLUTION_COMMENT
    return solution

@pytest.fixture
def zug_game(game):
    return ZugRoot(game)

@pytest.fixture
def zug_solution(solution, zug_game):
    return ZugSolution(solution, zug_game)

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
def ZugDataSubclass():
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
    def test_json(self, ZugDataSubclass, json, kwargs):
        # Translating to and from json works with a subset of parameters.
        zug_data = ZugDataSubclass(**kwargs)
        assert ZugDataSubclass.from_json(json) == zug_data
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
    def test_update(self, ZugDataSubclass, update_dict, expected_dict):
        # Updating with recognised arguments updates the object __dict__.
        zug_data = ZugDataSubclass()
        zug_data.update(update_dict)
        assert zug_data.__dict__ == expected_dict
        
    def test_update_foreign_attribute(self, ZugDataSubclass):
        # Updating with unrecognised arguments raises an exception.       
        zug_data = ZugDataSubclass()
        with pytest.raises(ZugDataError):
            zug_data.update({'unrecognised_key': 'any_value'})


class TestZugRootData:

    def test_defaults(self, default_root_data):
        assert ZugRootData() == default_root_data
    

class TestZugSolutionData:

    def test_defaults(self, default_solution_data):
        assert ZugSolutionData() == default_solution_data    


class TestZugRoot:

    def test_bind(self):
        game = chess.pgn.Game()
        game.comment = ALTERNATE_ROOT_COMMENT        
        zug_root = ZugRoot(game)
        
        game.comment = DEFAULT_ROOT_COMMENT
        zug_root._bind()
        assert game.comment == ALTERNATE_ROOT_COMMENT

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
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_REMAINING - 1,
            ),
            (
                YESTERDAY.isoformat(),
                DEFAULT_LEARNING_REMAINING,
                TODAY.isoformat(),
                DEFAULT_LEARNING_REMAINING,
            ),
            (
                YESTERDAY.isoformat(),
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_REMAINING,
            ),
            (
                PAST_EPOCH.isoformat(),
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY.isoformat(),
                DEFAULT_LEARNING_REMAINING,
            ),
        ],
        ids = [
            'no update',
            'update with identical learning_remaining',            
            'update with last_access yesterday',
            'update with last_access past_epoch',            
        ]
    )
    def test_update(
            self,
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
        # Decrementing a zero learning-remaining raises and exception
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


class TestZugSolution():

    def test_learned(self, game, solution, zug_game):

        zug_game.decrement_learning_remaining = mock.MagicMock()
        solution.comment = (
            '['
            '"due_date": "1999-12-31", '
            '"failures": 0, '
            '"last_study_date": "1999-12-31", '
            '"status": "UNLEARNED", '            
            '"successes": 0'
            ']'
        )
        zug_solution = ZugSolution(solution, zug_game)
        
        zug_solution.learned()
        
        zug_game.decrement_learning_remaining.assert_called_once()
        assert solution.comment == (
        '['
        '"due_date": "2000-01-02", '
        '"failures": 0, '
        '"last_study_date": "2000-01-01", '
        '"status": "LEARNED", '            
        '"successes": 1'
        ']'
        )

    def test_recalled(self, game, solution, zug_game):
        zug_game.decrement_learning_remaining = mock.MagicMock()
        ZugDates.due_date = mock.MagicMock(return_value = FUTURE_EPOCH)        
        solution.comment = (
            '['
            '"due_date": "2000-01-01", '
            '"failures": 0, '
            '"last_study_date": "1999-12-01", '
            '"status": "LEARNED", '            
            '"successes": 1'
            ']'
        )
        zug_solution = ZugSolution(solution, zug_game)
        
        zug_solution.recalled()
        
        zug_game.decrement_learning_remaining.assert_not_called()
        assert solution.comment == (
        '['
        '"due_date": "2000-04-10", '
        '"failures": 0, '
        '"last_study_date": "2000-01-01", '
        '"status": "LEARNED", '            
        '"successes": 2'
        ']'
        )

    def test_forgotten(self, solution):
        zug_game.decrement_learning_remaining = mock.MagicMock()
        ZugDates.due_date = mock.MagicMock(return_value = FUTURE_EPOCH)        
        solution.comment = (
            '['
            '"due_date": "2000-01-01", '
            '"failures": 0, '
            '"last_study_date": "1999-12-01", '
            '"status": "LEARNED", '            
            '"successes": 1'
            ']'
        )
        zug_solution = ZugSolution(solution, zug_game)
        
        zug_solution.forgotten()
        
        zug_game.decrement_learning_remaining.assert_not_called()
        assert solution.comment == (
        '['
        '"due_date": "2000-01-01", '
        '"failures": 1, '
        '"last_study_date": "1999-12-01", '
        '"status": "UNLEARNED", '            
        '"successes": 1'
        ']'
        )
    
    def test_remembered(self, solution):
        zug_game.decrement_learning_remaining = mock.MagicMock()
        ZugDates.due_date = mock.MagicMock(return_value = FUTURE_EPOCH)        
        solution.comment = (
            '['
            '"due_date": "2000-01-01", '
            '"failures": 1, '
            '"last_study_date": "1999-12-01", '
            '"status": "UNLEARNED", '            
            '"successes": 1'
            ']'
        )
        zug_solution = ZugSolution(solution, zug_game)
        
        zug_solution.remembered()
        
        zug_game.decrement_learning_remaining.assert_not_called()
        assert solution.comment == (
        '['
        '"due_date": "2000-01-02", '
        '"failures": 1, '
        '"last_study_date": "2000-01-01", '
        '"status": "LEARNED", '            
        '"successes": 2'
        ']'
        )
    
class RedundantTests:
    
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

