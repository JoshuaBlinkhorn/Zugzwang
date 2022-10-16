import pytest
import mock
import chess.pgn
import os

from zugzwang.game import (
    ZugData,
    ZugRootData,
    ZugSolutionData,
    ZugGameNodeWrapper,
    ZugRoot,
    ZugSolution,
    ZugDataError,
    ZugRootError,
)
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

# fix default solution data values
# define the path to the example category, which holds the example chapters
EXAMPLE_CATEGORY_PATH = os.path.join(
    os.getcwd(), "TestCollections/ExampleCollection/ExampleCategory"
)

@pytest.fixture
def default_root_data_white_perspective(default_root_data):
    return default_root_data


@pytest.fixture
def default_data_black_perspective(default_root_data):
    default_root_data.perspective = ZugColours.BLACK
    return default_root_data


@pytest.fixture
def zug_solution(solution, zug_game):
    return ZugSolution(solution, zug_game)


@pytest.fixture
def root_only_game():
    game = chess.pgn.Game()
    game.comment = ZugRootData().make_json()
    return game


@pytest.fixture
def ZugDataSubclass():
    """Fixture representing a typical ZugData subclass"""
    # This demonstates how to implement a ZugData subclass, including how to
    # handle typical default dates (recall how Pyhon handles default arguments).
    # It would be nice to be able to specify the class itself, rather than
    # implement it.
    # Perhaps we need a metaclass to do that..
    # But the current implementation is fit for purpose.

    class ZugDataSubclass(ZugData):
        def __init__(
            self,
            integer=0,
            floater=0.0,
            string="foobar",
            date=None,
        ):
            self.integer = integer
            self.floater = floater
            self.string = string
            self.date = date if date is not None else epoch_shift(0)

    return ZugDataSubclass


class TestZugData:
    """Unit tests for the ZugData class."""
    
    def test_from_json(self):
        """A ZugData object created from empty json is the default object"""        
        json = "{}"
        zug_data = ZugData.from_json(json)        
        assert zug_data == ZugData()

    def test_make_json(self):
        """Since a ZugData object has no attributes, the outputted json is empty"""
        zug_data = ZugData()
        expected_json = "{}"
        assert zug_data.make_json() == expected_json
    

    @pytest.mark.parametrize(
        "json, kwargs",
        [
            pytest.param(
                (
                    "{"
                    '"date": "2000-01-01", '
                    '"floater": 0.0, '
                    '"integer": 0, '
                    '"string": "foobar"'
                    "}"
                ),
                {},
                id='empty kwargs'
            ),
            pytest.param(
                (
                    "{"
                    '"date": "2000-01-01", '
                    '"floater": 100.0, '
                    '"integer": 100, '
                    '"string": "barfoo"'
                    "}"
                ),
                {
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                id="non-default non-date kwargs",                
            ),
            pytest.param(
                (
                    "{"
                    '"date": "2000-01-02", '
                    '"floater": 0.0, '
                    '"integer": 0, '
                    '"string": "foobar"'
                    "}"
                ),
                {
                    "date": epoch_shift(1),
                },
                id="non-default date kwarg",
            ),
        ],
    )
    def test_json(self, ZugDataSubclass, json, kwargs):
        """Translating to and from json works as expected"""
        zug_data = ZugDataSubclass(**kwargs)
        assert ZugDataSubclass.from_json(json) == zug_data
        assert zug_data.make_json() == json

    @pytest.mark.parametrize(
        "update_dict, expected_dict",
        [
            pytest.param(
                {},
                {
                    "date": epoch_shift(0),
                    "floater": 0.0,
                    "integer": 0,
                    "string": "foobar",
                },
                id="empty update" ,
            ),
            pytest.param(
                {
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                {
                    "date": epoch_shift(0),
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                id="update non-dates",                
            ),
            pytest.param(
                {
                    "date": epoch_shift(1),
                },
                {
                    "date": epoch_shift(1),
                    "floater": 0.0,
                    "integer": 0,
                    "string": "foobar",
                },
                id="update date",                
            ),
        ],
    )
    def test_update(self, ZugDataSubclass, update_dict, expected_dict):
        """Updating with recognised arguments updates the object __dict__"""
        zug_data = ZugDataSubclass()
        zug_data.update(update_dict)
        assert zug_data.__dict__ == expected_dict

    def test_update_foreign_attribute(self, ZugDataSubclass):
        """Updating with unrecognised arguments raises an exception"""
        zug_data = ZugDataSubclass()
        with pytest.raises(ZugDataError):
            zug_data.update({"unrecognised_key": "any_value"})


DEFAULT_PERSPECTIVE = ZugColours.WHITE
DEFAULT_LAST_ACCESS = TODAY
DEFAULT_LEARNING_REMAINING = 10
DEFAULT_LEARNING_LIMIT = 10
DEFAULT_RECALL_FACTOR = 2.0
DEFAULT_RECALL_RADIUS = 3
DEFAULT_RECALL_MAX = 365

@pytest.fixture
def default_root_data():
    """A default ZugRootData from explicitly given default values."""
    # We want to create this object explicity, rather than importing the defaults
    # or just using ZugRootData(), becuase we want to test that the default object is
    # exactly this one.
    # This merely provides an extra level of protection over the default definition.
    return ZugRootData(
        perspective=DEFAULT_PERSPECTIVE,
        last_access=DEFAULT_LAST_ACCESS,
        learning_remaining=DEFAULT_LEARNING_REMAINING,
        learning_limit=DEFAULT_LEARNING_LIMIT,
        recall_factor=DEFAULT_RECALL_FACTOR,
        recall_radius=DEFAULT_RECALL_RADIUS,
        recall_max=DEFAULT_RECALL_MAX,
    )


class TestZugRootData:
    """Unit tests for the ZugRootData class."""
    
    def test_defaults(self, default_root_data):
        """The default object is the expected one."""
        assert ZugRootData() == default_root_data


DEFAULT_STATUS = ZugSolutionStatuses.UNLEARNED
DEFAULT_LAST_STUDY_DATE = YESTERDAY
DEFAULT_DUE_DATE = YESTERDAY
DEFAULT_SUCCESSES = 0
DEFAULT_FAILURES = 0

@pytest.fixture
def default_solution_data():
    """A default ZugSolutionData from explicitly given default values."""
    # We want to create this object explicity, rather than importing the defaults
    # or just using ZugSolutionData(), becuase we want to test that the default
    # object is exactly this one.
    # This merely provides an extra level of protection over the default definition.
    return ZugSolutionData(
        status=DEFAULT_STATUS,
        last_study_date=DEFAULT_LAST_STUDY_DATE,
        due_date=DEFAULT_DUE_DATE,
        successes=DEFAULT_SUCCESSES,
        failures=DEFAULT_FAILURES,
    )


class TestZugSolutionData:
    """Unit tests for the ZugSolutionData class."""
    
    def test_defaults(self, default_solution_data):
        """The default object is the expected one."""        
        assert ZugSolutionData() == default_solution_data


@pytest.fixture
def ZugGameNodeWrapperSubclass(ZugDataSubclass):
    """Fixture representing a typical ZugGameNodeWrapper subclass"""

    class ZugGameNodeWrapperSubclass(ZugGameNodeWrapper):
        _data_class = ZugDataSubclass

    return ZugGameNodeWrapperSubclass


class TestZugGameNodeWrapper:
    """Unit tests for the ZugGameNodeWrapper class."""

    def test_bind(self, ZugGameNodeWrapperSubclass):
        """The node's comment is populated with json generated by the data class."""
        
        # Create a basic game node with and empty comment, and wrap it.
        node = chess.pgn.Game()
        node.comment = '[]'
        wrapper = ZugGameNodeWrapperSubclass(node)

        # Determine what the comment should hold after binding.
        # This does not depend on the comment's current value.
        default_json = wrapper.data.make_json()
        expected_comment = default_json.replace('{', '[').replace('}', ']')        

        # Bind the data to the node's comment
        wrapper.bind()

        # Check it has the desired effect
        assert node.comment == expected_comment
        

class TestZugRoot:
    """Unit tests for the ZugGameNodeWrapper class."""

    @pytest.mark.parametrize(
        (
            "last_access, "
            "learning_remaining, "
            "expected_last_access, "
            "expected_learning_remaining"
        ),
        [
            pytest.param(
                TODAY,
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY,
                DEFAULT_LEARNING_REMAINING - 1,
                id="last access today",
            ),
            pytest.param(
                YESTERDAY,
                DEFAULT_LEARNING_REMAINING,
                TODAY,
                DEFAULT_LEARNING_REMAINING,
                id="last access yesterday, learning remaining unchanged",
            ),
            pytest.param(
                YESTERDAY,
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY,
                DEFAULT_LEARNING_REMAINING,
                id="last access yesterday, learning remaining changed",
            ),
            pytest.param(
                PAST_EPOCH,
                DEFAULT_LEARNING_REMAINING - 1,
                TODAY,
                DEFAULT_LEARNING_REMAINING,
                id="last access in past, learning remaining changed",                
            ),
        ],
    )
    def test_update(
        self,
        last_access,
        learning_remaining,
        expected_last_access,
        expected_learning_remaining,
    ):
        """
        If the last access is prior to today, update the learning_remaing and
        last_access fields of the root's data.
        """

        # Set up a game node with the initial comment, based on test parameters,
        # and wrap it with a root
        game = chess.pgn.Game()
        game.comment = (
            "["
            f'"last_access": "{last_access.isoformat()}", '
            '"learning_limit": 10, '
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '
            '"recall_radius": 3'
            "]"
        )
        root = ZugRoot(game)
        root.bind = mock.MagicMock()
        
        # Form the expected comment after update
        expected_data = ZugRootData(
            last_access=expected_last_access,
            learning_limit=10,
            learning_remaining=expected_learning_remaining,
            perspective=ZugColours.WHITE,
            recall_factor=2.0,
            recall_max=365,
            recall_radius=3,
        )

        # Update the root
        root.update()

        # Check the game comment is as expected
        assert root.data == expected_data
        root.bind.assert_called_once()


    @pytest.mark.parametrize(
        "learning_remaining, expected_learning_remaining",
        [
            pytest.param(1, 0, id="smallest"),
            pytest.param(2, 1, id="small"),
            pytest.param(10, 9, id="medium"),
            pytest.param(1000, 999, id="large")
        ],
    )
    def test_decrement_learning_remaining(
        self, learning_remaining, expected_learning_remaining
    ):
        """Learning remaining is decremented if it is positive."""
        game = chess.pgn.Game()
        game.comment = (
            "["
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '
            '"recall_radius": 3'
            "]"
        )
        root = ZugRoot(game)
        root.bind = mock.MagicMock()

        expected_data = ZugRootData(
            last_access=TODAY,
            learning_limit=10,
            learning_remaining=expected_learning_remaining,
            perspective=ZugColours.WHITE,
            recall_factor=2.0,
            recall_max=365,
            recall_radius=3
        )

        root.decrement_learning_remaining()
        assert root.data == expected_data
        root.bind.assert_called_once()

    def test_decrement_zero_learning_remaining(self):
        """Decrementing a non-positive learning_remaining raises an exception."""
        
        game = chess.pgn.Game()
        game.comment = (
            "["
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '
            '"learning_remaining": 0, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '
            '"recall_radius": 3'
            "]"
        )
        root = ZugRoot(game)
        with pytest.raises(ZugRootError):
            root.decrement_learning_remaining()

    @pytest.mark.parametrize(
        "learning_remaining, expected_has_learning_capacity",
        [
            pytest.param(0, False, id="zero"),
            pytest.param(1, True, id="small"),
            pytest.param(2, True, id="medium"),
            pytest.param(100, True, id="large")
        ],
    )
    def test_has_learning_capacity(
        self, learning_remaining, expected_has_learning_capacity
    ):
        """Returns true if and only if the learning remaining is positive."""
        
        game = chess.pgn.Game()
        game.comment = (
            "["
            '"last_access": "2000-01-01", '
            '"learning_limit": 10, '
            f'"learning_remaining": {learning_remaining}, '
            '"perspective": true, '
            '"recall_factor": 2.0, '
            '"recall_max": 365, '
            '"recall_radius": 3'
            "]"
        )
        root = ZugRoot(game)

        assert root.has_learning_capacity() == expected_has_learning_capacity


DEFAULT_ROOT_COMMENT = (
    "["
    '"last_access": "2000-01-01", '
    '"learning_limit": 10, '
    '"learning_remaining": 10, '
    '"perspective": true, '
    '"recall_factor": 3.0, '
    '"recall_max": 365, '
    '"recall_radius": 3'
    "]"
)

DEFAULT_SOLUTION_COMMENT = (
    "["
    '"status": "LEARNED", '
    '"last_study_date": "1999-12-31", '
    '"due_date": "1999-12-31", '
    '"successes": 0, '
    '"failures": 0'
    "]"
)

@pytest.fixture
def game():
    game = chess.pgn.Game()
    game.comment = DEFAULT_ROOT_COMMENT
    return game


@pytest.fixture
def solution_node(game):
    solution_node = game.add_variation(chess.Move.from_uci("e2e4"))
    solution_node.comment = DEFAULT_SOLUTION_COMMENT
    return solution_node


@pytest.fixture
def root(game):
    root = ZugRoot(game)
    root.decrement_learning_remaining = mock.MagicMock()
    return root


class TestZugSolution:
    """Unit tests for the ZugSolution class."""
    
    def test_learned(self, game, solution_node, root):
        """
        When a solution is learned:
        - the status is set to LEARNED;
        - the due date is set as tomorrow; 
        - successes is incremented;
        - the root's learning remaining is decremented;
        """

        # Set the solution nodes comment, and generate the wrapper
        solution_node.comment = (
            "["
            f'"due_date": "{YESTERDAY.isoformat()}", '
            '"failures": 0, '
            f'"last_study_date": "{YESTERDAY.isoformat()}", '
            '"status": "UNLEARNED", '
            '"successes": 0'
            "]"
        )
        solution = ZugSolution(solution_node, root)
        solution.bind = mock.MagicMock()

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=TOMORROW,
            failures=0,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=1
        )

        # Call the tested method
        solution.learned()

        # Check the results
        assert solution.data == expected_data
        solution.bind.assert_called_once()
        root.decrement_learning_remaining.assert_called_once()

    def test_recalled(self, game, solution_node, root):
        """
        When a solution is recalled:
        - the status remains as LEARNED;
        - the due date is set in the future; 
        - successes is incremented;
        - the root's learning remaining is not decremented;
        """

        # Mock out the call to ZugDates.due_date().
        # That method calculates a due date with an element of probability.
        # So we fix its output.
        ZugDates.due_date = mock.MagicMock(return_value=FUTURE_EPOCH)

        # Edit the solution comment and generate the wrapper
        solution_node.comment = (
            "["
            '"due_date": "2000-01-01", '
            '"failures": 0, '
            '"last_study_date": "1999-12-01", '
            '"status": "LEARNED", '
            '"successes": 1'
            "]"
        )
        solution = ZugSolution(solution_node, root)
        solution.bind = mock.MagicMock()

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=FUTURE_EPOCH,
            failures=0,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=2,
        )
        
        # Call the tested method
        solution.recalled()

        # Check the results
        assert solution.data == expected_data
        solution.bind.assert_called_once()
        root.decrement_learning_remaining.assert_not_called()

    def test_forgotten(self, solution_node, root):
        """
        When a solution is forgotten:
        - the status is set to UNLEARNED;
        - failures is incremented;
        - the root's learning remaining is not decremented;
        """
        
        # Set the solution node comment and generate the wrapper
        solution_node.comment = (
            "["
            f'"due_date": "{TODAY.isoformat()}", '
            '"failures": 0, '
            f'"last_study_date": "{PAST_EPOCH.isoformat()}", '
            '"status": "LEARNED", '
            '"successes": 1'
            "]"
        )
        solution = ZugSolution(solution_node, root)
        solution.bind = mock.MagicMock()

        # Describe expected data
        expected_data = ZugSolutionData(
            due_date=TODAY,
            failures=1,
            last_study_date=PAST_EPOCH,
            status=ZugSolutionStatuses.UNLEARNED,
            successes=1,
        )

        # Call the tested method
        solution.forgotten()        

        # Check the results
        assert solution.data == expected_data
        solution.bind.assert_called_once()
        root.decrement_learning_remaining.assert_not_called()


    def test_remembered(self, solution_node, root):
        """
        When a solution is forgotten:
        - the status is set to LEARNED;
        - the due date is set to tomorrow;
        - successes is incremented;
        - the root's learning remaining is not decremented;
        """

        # Edit solution comment and generate wrapper
        ZugDates.due_date = mock.MagicMock(return_value=FUTURE_EPOCH)
        solution_node.comment = (
            "["
            '"due_date": "{TODAY.isoformat()}", '
            '"failures": 1, '
            '"last_study_date": "PAST_EPOCH.isoformat()", '
            '"status": "UNLEARNED", '
            '"successes": 1'
            "]"
        )
        solution = ZugSolution(solution_node, root)
        solution.bind = mock.MagicMock()

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=TOMORROW,
            failures=1,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=2
        )
        
        # Call the tested method
        solution.remembered()

        # Check the results
        assert solution.data == expected_data
        solution.bind.assert_called_once()
        root.decrement_learning_remaining.assert_not_called()


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
