import pytest
import unittest
import mock
import datetime
import chess.pgn
from conftest import epoch_shift

from zugzwang.queue import (
    ZugQueue,
    ZugQueueItem,
    ZugTrainingPosition,
    ZugTrainingPositionPresenter,
)
from zugzwang.game import (
    ZugSolutionData,
    ZugSolutionStatuses,
)

TODAY = epoch_shift(0)
YESTERDAY = epoch_shift(-1)
TOMORROW = epoch_shift(1)
PAST_EPOCH = epoch_shift(-1000)
FUTURE_EPOCH = epoch_shift(1000)

FAILURES = 5
SUCCESSES = 5

@pytest.fixture
def solution_data():
    return ZugSolutionData(
        status = ZugSolutionStatuses.INACTIVE,
        last_study_date = datetime.date(day=1, month=1, year=2000),
        due_date = datetime.date(day=1, month=1, year=2001),
        successes = 10,
        failures = 0,
    )

@pytest.fixture
def solution_node():
    root = chess.pgn.Game()
    move = chess.Move.from_uci('e2e4')
    problem_node = chess.pgn.ChildNode(root, move)
    move = chess.Move.from_uci('e7e5')
    solution_node = chess.pgn.ChildNode(problem_node, move)
    return solution_node

def test_ZuqQueueItem_play():
    # the base class's play() method returns None
    # the present method returns
    assert ZugQueueItem().play() == None


def testZugTrainingPosition_play_solution_status_inactive(solution_node):
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.INACTIVE,
        last_study_date = datetime.date(day=1, month=1, year=2000),
        due_date = datetime.date(day=1, month=1, year=2001),
        successes = 10,
        failures = 0,
    )
    solution_node.comment = solution_data.make_comment()

    with pytest.raises(Exception):
        ZugTrainingPosition(solution_node)
    

@pytest.mark.parametrize(
    'status, presenter_result, expected_solution_data, expected_is_reinsertable',
    [
        (
            ZugSolutionStatuses.NEW,
            ZugTrainingPositionPresenter.SUCCESS,
            ZugSolutionData(
                status = ZugSolutionStatuses.LEARNING_STAGE_1,
                last_study_date = YESTERDAY,
                due_date = YESTERDAY,
                successes = SUCCESSES,
                failures = FAILURES,
            ),
            ZugQueue.REINSERT,
        ),
        (
            ZugSolutionStatuses.LEARNING_STAGE_1,
            ZugTrainingPositionPresenter.SUCCESS,
            ZugSolutionData(
                status = ZugSolutionStatuses.LEARNING_STAGE_2,
                last_study_date = YESTERDAY,
                due_date = YESTERDAY,
                successes = SUCCESSES,
                failures = FAILURES,
            ),
            ZugQueue.REINSERT,
        ),
        (
            ZugSolutionStatuses.LEARNING_STAGE_1,
            ZugTrainingPositionPresenter.FAILURE,
            ZugSolutionData(
                status = ZugSolutionStatuses.LEARNING_STAGE_1,
                last_study_date = YESTERDAY,
                due_date = YESTERDAY,
                successes = SUCCESSES,
                failures = FAILURES,
            ),
            ZugQueue.REINSERT,
        ),
        (
            ZugSolutionStatuses.LEARNING_STAGE_2,
            ZugTrainingPositionPresenter.SUCCESS,
            ZugSolutionData(
                status = ZugSolutionStatuses.REVIEW,
                last_study_date = TODAY,
                due_date = TOMORROW,
                successes = SUCCESSES + 1,
                failures = FAILURES,
            ),
            ZugQueue.DISCARD,
        ),
        (
            ZugSolutionStatuses.LEARNING_STAGE_2,
            ZugTrainingPositionPresenter.FAILURE,
            ZugSolutionData(
                status = ZugSolutionStatuses.LEARNING_STAGE_1,
                last_study_date = YESTERDAY,
                due_date = YESTERDAY,
                successes = SUCCESSES,
                failures = FAILURES,
            ),
            ZugQueue.REINSERT,
        ),
    ]
)
def test_ZugTrainingPosition_play_learning_phase(
        solution_node,
        status,
        presenter_result,
        expected_solution_data,
        expected_is_reinsertable,
):
    # create a typical solution node
    solution_data = ZugSolutionData(
        status = status,
        last_study_date = YESTERDAY,
        due_date = YESTERDAY,
        successes = SUCCESSES,
        failures = FAILURES,
    )
    solution_node.comment = solution_data.make_comment()

    # create the training position, mocking out the presenter
    tp = ZugTrainingPosition(solution_node)
    tp._presenter.present = mock.MagicMock(return_value=presenter_result)

    # call
    is_reinsertable = tp.play()

    # assert the expected change to the solution data
    # and the function call return value
    assert tp.solution_data == expected_solution_data
    assert is_reinsertable == expected_is_reinsertable

def test_ZugTrainingPosition_play_review_phase_failure(solution_node):
    # create a typical solution node
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.REVIEW,
        last_study_date = YESTERDAY,
        due_date = TODAY,
        successes = SUCCESSES,
        failures = FAILURES,
    )
    solution_node.comment = solution_data.make_comment()

    # create the training position, mocking out the presenter
    tp = ZugTrainingPosition(solution_node)
    tp._presenter.present = mock.MagicMock(
        return_value=ZugTrainingPositionPresenter.FAILURE
    )

    # call
    is_reinsertable = tp.play()

    # assert the expected change to the solution node comment
    # and the function call return value
    updated_solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.LEARNING_STAGE_1,
        last_study_date = YESTERDAY,
        due_date = TODAY,
        successes = SUCCESSES,
        failures = FAILURES + 1,
    )
    expected_comment = updated_solution_data.make_comment()
    assert tp.solution_data == updated_solution_data
    assert is_reinsertable == ZugQueue.REINSERT

@pytest.mark.parametrize(
    'last_study_date, due_date_lower_bound, due_date_upper_bound',
    [
        (
            YESTERDAY,
            TOMORROW,
            TOMORROW + datetime.timedelta(days = 2),
        ),
        (
            TODAY - datetime.timedelta(days = 2),
            TODAY + datetime.timedelta(days = 2),
            TODAY + datetime.timedelta(days = 6),                        
        ),
        (
            TODAY - datetime.timedelta(days = 10),
            TODAY + datetime.timedelta(days = 17),
            TODAY + datetime.timedelta(days = 23),                        
        ),
    ]
)
def test_ZugTrainingPosition_play_review_phase_success(
        solution_node,
        last_study_date,
        due_date_lower_bound,
        due_date_upper_bound,
):
    # create a typical solution node
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.REVIEW,
        last_study_date = last_study_date,
        due_date = TODAY,
        successes = SUCCESSES,
        failures = FAILURES,
    )
    solution_node.comment = solution_data.make_comment()

    # create the training position, mocking out the presenter
    tp = ZugTrainingPosition(solution_node)
    tp._presenter.present = mock.MagicMock(
        return_value=ZugTrainingPositionPresenter.SUCCESS
    )

    # call
    is_reinsertable = tp.play()

    # convert the solution node's comment into solution data
    updated_solution_data = tp.solution_data

    # assert the updated solution data, and hence the node's comment, is correct
    # the important point here is that the new due date is within the expected range
    assert updated_solution_data.status == ZugSolutionStatuses.REVIEW
    assert updated_solution_data.last_study_date == TODAY
    assert updated_solution_data.due_date >= due_date_lower_bound
    assert updated_solution_data.due_date <= due_date_upper_bound
    assert updated_solution_data.successes == SUCCESSES + 1
    assert updated_solution_data.failures == FAILURES    
    assert is_reinsertable == ZugQueue.DISCARD
