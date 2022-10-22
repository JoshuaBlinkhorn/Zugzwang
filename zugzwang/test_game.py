import pytest
import mock
import chess.pgn
import os
import json

from zugzwang.game import (
    ZugData,
    ZugRootData,
    ZugSolutionData,
    ZugGameNodeWrapper,
    ZugGameNodeWrapperError,
    ZugRoot,
    ZugSolution,
    ZugDataError,
    ZugDataDecodeError,
    ZugDataFieldError,    
    ZugRootError,
)
from zugzwang.constants import ZugColours, ZugSolutionStatuses
from zugzwang.dates import ZugDates
from zugzwang.conftest import epoch_shift
from zugzwang.tools import ZugStringTools, ZugJsonTools

# Fix a mock today and dates relative to it
PAST_EPOCH = epoch_shift(-100)
YESTERDAY = epoch_shift(-1)
TODAY = epoch_shift(0)
TOMORROW = epoch_shift(1)
FUTURE_EPOCH = epoch_shift(100)

###########
# ZugData #
###########


@pytest.fixture
def MyZugData():
    """Fixture representing a typical ZugData subclass"""
    # This demonstates how to implement a ZugData subclass, including how to
    # handle typical default dates (recall how Pyhon handles default arguments).
    # It would be nice to be able to specify the class itself, rather than
    # implement it.
    # Perhaps we need a metaclass to do that..
    # But the current implementation is fit for purpose.

    class MyZugData(ZugData):
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

    return MyZugData


class TestZugData:
    """Unit tests for the ZugData class."""

    @pytest.mark.parametrize(
        "data_dict, expected_attributes",
        [
            pytest.param(
                {},
                {
                    "date": TODAY,
                    "floater": 0.0,
                    "integer": 0,
                    "string": "foobar",
                },
                id="empty json",
            ),
            pytest.param(
                {
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                {
                    "date": TODAY,
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo"
                },
                id="partial json no date",
            ),
            pytest.param(
                {
                    "date": TOMORROW,
                },
                {
                    "date": TOMORROW,
                    "floater": 0.0,
                    "integer": 0,
                    "string": "foobar"
                },
                id="partial json with date",
            ),
            pytest.param(
                {
                    "date": TODAY, 
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                {
                    "date": TODAY,
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo"
                },
                id="complete json",
            ),
        ],
    )
    def test_constructor(self, MyZugData, data_dict, expected_attributes):
        """Fields not supplied as kwargs are filled in with defaults."""
        zug_data = MyZugData(**data_dict)
        for attribute, value in expected_attributes.items():
            assert getattr(zug_data, attribute) == value

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
                id="empty update",
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
    def test_update(self, MyZugData, update_dict, expected_dict):
        """Updating with recognised arguments updates the object __dict__"""
        zug_data = MyZugData()
        zug_data.update(update_dict)
        assert zug_data.__dict__ == expected_dict

    def test_update_foreign_attribute(self, MyZugData):
        """Updating with unrecognised field raises an exception"""
        zug_data = MyZugData()
        with pytest.raises(ZugDataFieldError):
            zug_data.update({"unrecognised_key": "any_value"})

    def test_as_dict(self, MyZugData):
        """The data dict is returned."""
        expected_dict = {
            "date": TODAY,
            "floater": 0.0,
            "integer": 0,
            "string": "foobar"
        }
        assert MyZugData().as_dict() == expected_dict

    def test_as_string(self, MyZugData):
        """
        The correctly-formatted 'zug-string' is returned.

        The 'zug-string' is similar to json serialisation of a dictionary, except
        that the delimiting curly braces are straight. This is needed to avoid
        pgn parsing bugs with curly braces inside comments, which are themselves
        delimited by curly braces in the PGN standard.

        Dates are encoded in ISO format.
        """
        # default values of MyZugData in constructor order, strings double-quoted
        expected_string = (
        '['
            '"integer": 0, '
            '"floater": 0.0, '
            '"string": "foobar", '
            f'"date": "{TODAY.isoformat()}"'
        ']'
        )
        assert MyZugData().as_string() == expected_string

    @pytest.mark.parametrize(
        'zug_string, kwargs',
        [
            pytest.param(
                '[]',
                {},
                id='empty'
            ),
            pytest.param(
                (
                    '['
                    '"integer": 100, '
                    f'"date": "{TOMORROW.isoformat()}"'
                    ']'
                ),
                {
                    "integer": 100,
                    "date": TOMORROW,
                },
                id='partial'
            ),
            pytest.param(
                (
                    '['
                    '"integer": 100, '
                    '"floater": 100.0, '
                    '"string": "barfoo", '
                    f'"date": "{TOMORROW.isoformat()}"'
                    ']'
                ),
                {
                    "integer": 100,
                    "floater": 100.0,
                    "string": "barfoo",
                    "date": TOMORROW,
                },
                id='complete'
            ),
        ]
    )
    def test_from_string(self, zug_string, kwargs, MyZugData):
        """Creates a data object from a 'zug-string'."""
        assert MyZugData.from_string(zug_string) == MyZugData(**kwargs)

    @pytest.mark.parametrize(
        'invalid_string',
        [
            pytest.param(
                '{}',
                id='empty curly braces'
            ),
            pytest.param(
                '{"string": "barfoo"}',
                id='non empty curly braces'
            ),
            pytest.param(
                'adshfapishfn',
                id='gobbledygook'
            ),
            pytest.param(
                '["string": "barfoo" "integer": 0]',
                id='badly formatted square braces'
            ),            
        ]
    )
    def test_from_string_invalid_string(self, invalid_string, MyZugData):
        with pytest.raises(ZugDataDecodeError):
            MyZugData.from_string(invalid_string)

    @pytest.mark.parametrize(
        'data_dict',
        [
            pytest.param(
                {},
                id='empty'
            ),
            pytest.param(
                {
                    "integer": 100,
                    "date": TOMORROW,
                },
                id='partial'
            ),
            pytest.param(
                {
                    "integer": 100,
                    "floater": 100.0,
                    "string": "barfoo",
                    "date": TOMORROW,
                },
                id='complete'
            ),
        ]
    )
    def test_from_dict(self, data_dict, MyZugData):
        """Creates a data object from a dict."""

        # An entirely ridiculous tests.
        # This method is merely an alias to provide symmetry in the interface;
        # so you can do from_dict() like you can from_string().
        # Of course we implement this exactly as the test reads.
        # It is tested merely on principle; it is a provided method, we should
        # make sure we don't inadvertently break it.
        assert MyZugData.from_dict(data_dict) == MyZugData(**data_dict)

    def test_equality(self, MyZugData):
        """Two objects compare as equal if, and only if, their data fields agree"""
        this = MyZugData()
        that = MyZugData()
        assert this == that

        this.floater = 100.0
        assert this != that

        that.floater = 100.0
        assert this == that        


###############
# ZugRootData #
###############

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
    # or just using ZugRootData(), because we want to test that the default object is
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


###################
# ZugSolutionData #
###################

DEFAULT_STATUS = ZugSolutionStatuses.UNLEARNED
DEFAULT_LAST_STUDY_DATE = YESTERDAY
DEFAULT_DUE_DATE = YESTERDAY
DEFAULT_SUCCESSES = 0
DEFAULT_FAILURES = 0


@pytest.fixture
def default_solution_data():
    """A default ZugSolutionData from explicitly given default values."""
    # We want to create this object explicity, rather than importing the defaults
    # or just using ZugSolutionData(), because we want to test that the default
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


######################
# ZugGameNodeWrapper #
######################

@pytest.fixture
def MyZugGameNodeWrapper(MyZugData):
    """Fixture representing a typical ZugGameNodeWrapper subclass"""

    class MyZugGameNodeWrapper(ZugGameNodeWrapper):
        _data_class = MyZugData

    return MyZugGameNodeWrapper


class TestZugGameNodeWrapper:
    """Unit tests for the ZugGameNodeWrapper class."""

    def test_constructor_no_game_comment(self, MyZugGameNodeWrapper, MyZugData):
        """
        If an uncommented node is supplied, default data is generated and written
        to the comment.
        """

        # Setup
        node = chess.pgn.Game()        
        zug_data = MyZugData()
        json_string = ZugJsonTools.encode(zug_data.as_dict())
        expected_comment = ZugStringTools.to_square_braces(json_string)

        # Create the wrapper
        assert node.comment == ''
        wrapper = MyZugGameNodeWrapper(node)

        # Assert that the wrapper's data and node's comment are the defaults
        assert wrapper.data == zug_data
        assert node.comment == expected_comment

    @pytest.mark.parametrize(
        'invalid_comment',
        [
            pytest.param('foobar', id='gbbledygook'),
            pytest.param('{}', id='curly braces'),
            pytest.param('["string": "foobar" "integer": 0]', id='badly formatted'),
        ]
    )
    def test_constructor_invalid_game_node_comment(
            self,
            invalid_comment,
            MyZugGameNodeWrapper
    ):
        """If the supplied game node has an invalid comment, an exception is raised."""
        
        # Setup
        game_node = chess.pgn.Game()
        game_node.comment = invalid_comment

        # Create the wrapper
        with pytest.raises(ZugGameNodeWrapperError):
            wrapper = MyZugGameNodeWrapper(game_node)

    @pytest.mark.parametrize(
        'partial_data_dict',
        [
            pytest.param(
                {},
                id='empty dict'
            ),
            pytest.param(
                {
                    'floater': 100.0,
                    'integer': 100,
                },
                id='partial dict without dates'
            ),
            pytest.param(
                {
                    'date': TOMORROW,
                },
                id='partial dict with dates'
            ),
            pytest.param(
                {
                    "date": TOMORROW,
                    "floater": 100.0,
                    "integer": 100,
                    "string": "barfoo",
                },
                id='complete dict'
            ),
        ]
    )
    def test_constructor_game_comment(
            self,
            partial_data_dict,
            MyZugGameNodeWrapper,
            MyZugData,
    ):
        """
        If an commented node is supplied, and the comment is valid, the wrapper's data
        is generated correctly.

        A valid comment may contain a subset of the known fields, in which case the
        missing fields should be filled in with defaults. This ensures backwards
        compatibility for adding new fields.
        """
        
        # Setup
        game_node = chess.pgn.Game()
        json_string = ZugJsonTools.encode(partial_data_dict)
        game_node.comment = ZugStringTools.to_square_braces(json_string)

        # formulate expectations
        expected_data = MyZugData(**partial_data_dict)
        json_string = ZugJsonTools.encode(expected_data.as_dict())
        expected_comment = ZugStringTools.to_square_braces(json_string)        

        # Create the wrapper
        wrapper = MyZugGameNodeWrapper(game_node)

        # Assert that the wrapper's data and node's comment are as expected
        assert wrapper.data == expected_data
        assert wrapper.game_node.comment == expected_comment


class TestZugRoot:
    """Unit tests for the ZugRoot class."""

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
        If the last access is prior to today, update the learning_remaining and
        last_access fields of the root's data.
        """

        # Set up a game node with the initial comment, based on test parameters,
        # and wrap it with a root
        game_node = chess.pgn.Game()
        data_dict = {
            "last_access": last_access,
            "learning_remaining": learning_remaining,
        }
        json_string = ZugJsonTools.encode(ZugRootData(**data_dict).as_dict())
        game_node.comment = ZugStringTools.to_square_braces(json_string)
        
        root = ZugRoot(game_node)

        # Form the expected comment after update
        expected_data = ZugRootData(
            last_access=expected_last_access,
            learning_remaining=expected_learning_remaining,
        )
        json_string = ZugJsonTools.encode(expected_data.as_dict())
        expected_comment = ZugStringTools.to_square_braces(json_string)

        # Update the root
        root.update()

        # Check the game comment is as expected
        assert root.data == expected_data
        assert root.game_node.comment == expected_comment

    @pytest.mark.parametrize(
        "learning_remaining, expected_learning_remaining",
        [
            pytest.param(1, 0, id="smallest"),
            pytest.param(2, 1, id="small"),
            pytest.param(10, 9, id="medium"),
            pytest.param(1000, 999, id="large"),
        ],
    )
    def test_decrement_learning_remaining(
        self, learning_remaining, expected_learning_remaining
    ):
        """Learning remaining is decremented if it is positive."""

        # Set up a game node and comment
        game_node = chess.pgn.Game()
        root_data = ZugRootData(learning_remaining=learning_remaining)
        game_node.comment = root_data.as_string()

        # Describe the expected data and comment
        expected_data = ZugRootData(learning_remaining=expected_learning_remaining)
        expected_comment = expected_data.as_string()

        # Create a root and call the tested function
        root = ZugRoot(game_node)
        root.decrement_learning_remaining()

        # The root's data and game node's comment are updated as expected
        assert root.data == expected_data
        assert root.game_node.comment == expected_comment

    def test_decrement_zero_learning_remaining(self):
        """Decrementing a non-positive learning_remaining raises an exception."""

        game = chess.pgn.Game()
        root_data = ZugRootData(learning_remaining=0)
        game.comment = root_data.as_string()

        root = ZugRoot(game)
        with pytest.raises(ZugRootError):
            root.decrement_learning_remaining()

    @pytest.mark.parametrize(
        "learning_remaining, expected_has_learning_capacity",
        [
            pytest.param(0, False, id="zero"),
            pytest.param(1, True, id="small"),
            pytest.param(2, True, id="medium"),
            pytest.param(100, True, id="large"),
        ],
    )
    def test_has_learning_capacity(
        self, learning_remaining, expected_has_learning_capacity
    ):
        """Returns true if and only if the learning remaining is positive."""

        game = chess.pgn.Game()
        root_data = ZugRootData(learning_remaining=learning_remaining)
        game.comment = root_data.as_string()

        root = ZugRoot(game)
        assert root.has_learning_capacity() == expected_has_learning_capacity


@pytest.fixture
def game():
    game = chess.pgn.Game()
    game.comment = ZugRootData().as_string()
    return game


@pytest.fixture
def solution_node(game):
    solution_node = game.add_variation(chess.Move.from_uci("e2e4"))
    solution_node.comment = ZugSolutionData().as_string()
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

        # Set the solution node's comment, and generate the wrapper
        solution_data = ZugSolutionData(
            due_date=TODAY,
            last_study_date=YESTERDAY,
            status=ZugSolutionStatuses.UNLEARNED,
            failures=0,
            successes=0,            
        )
        solution_node.comment = solution_data.as_string()

        solution = ZugSolution(solution_node, root)

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=TOMORROW,
            failures=0,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=1,
        )
        expected_comment = expected_data.as_string()

        # Call the tested method
        solution.learned()

        # Check the results
        assert solution.data == expected_data
        assert solution.game_node.comment == expected_comment
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
        solution_data = ZugSolutionData(
            due_date=TODAY,
            last_study_date=PAST_EPOCH,
            status=ZugSolutionStatuses.LEARNED,
            failures=0,
            successes=1,            
        )
        solution_node.comment = solution_data.as_string()

        solution = ZugSolution(solution_node, root)

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=FUTURE_EPOCH,
            failures=0,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=2,
        )
        expected_comment = expected_data.as_string()

        # Call the tested method
        solution.recalled()

        # Check the results
        assert solution.data == expected_data
        assert solution.game_node.comment == expected_comment
        root.decrement_learning_remaining.assert_not_called()        

    def test_forgotten(self, solution_node, root):
        """
        When a solution is forgotten:
        - the status is set to UNLEARNED;
        - failures is incremented;
        - the root's learning remaining is not decremented;
        """

        # Set the solution node comment and generate the wrapper
        solution_data = ZugSolutionData(
            due_date=TODAY,
            last_study_date=PAST_EPOCH,
            status=ZugSolutionStatuses.LEARNED,
            failures=0,
            successes=1,
        )
        solution_node.comment = solution_data.as_string()

        solution = ZugSolution(solution_node, root)

        # Describe expected data
        expected_data = ZugSolutionData(
            due_date=TODAY,
            last_study_date=PAST_EPOCH,            
            failures=1,
            status=ZugSolutionStatuses.UNLEARNED,
            successes=1,
        )
        expected_comment = expected_data.as_string()

        # Call the tested method
        solution.forgotten()

        # Check the results
        assert solution.data == expected_data
        assert solution.game_node.comment == expected_comment
        root.decrement_learning_remaining.assert_not_called()

    def test_remembered(self, solution_node, root):
        """
        When a solution is forgotten:
        - the status is set to LEARNED;
        - the due date is set to tomorrow;
        - successes is incremented;
        - the root's learning remaining is not decremented;
        """

        # Mock out the call to ZugDates.due_date().
        # That method calculates a due date with an element of probability.
        # So we fix its output.
        ZugDates.due_date = mock.MagicMock(return_value=FUTURE_EPOCH)

        # Write the solution node's comment and create the solution
        solution_data = ZugSolutionData(
            due_date=TODAY,
            last_study_date=PAST_EPOCH,
            status=ZugSolutionStatuses.UNLEARNED,
            failures=1,
            successes=1,
        )
        solution_node.comment = solution_data.as_string()
        solution = ZugSolution(solution_node, root)

        # Describe the expected data
        expected_data = ZugSolutionData(
            due_date=TOMORROW,
            failures=1,
            last_study_date=TODAY,
            status=ZugSolutionStatuses.LEARNED,
            successes=2,
        )
        expected_comment = expected_data.as_string()

        # Call the tested method
        solution.remembered()

        # Check the results
        assert solution.data == expected_data
        assert solution.game_node.comment == expected_comment
        root.decrement_learning_remaining.assert_not_called()
