import pytest
import unittest
import mock
import datetime
import chess.pgn

from zugzwang import (
    ZugQueueItem,
    ZugTrainingPosition,
    ZugSolutionData,
    ZugSolutionStatuses,
    ZugSolutionStatusError,
)

@pytest.fixture
def solution_data():
    return ZugSolutionData(
        status = ZugSolutionStatuses.INACTIVE,
        previous_date = datetime.date(day=1, month=1, year=2000),
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
    #solution_node.comment = solution_data.make_comment()
    return solution_node

def test_ZuqQueueItem_play():
    # the bass class's play() method returns None
    # the present method returns
    assert ZugQueueItem().play() == None


def testZugTrainingPosition_play_inactive_solution_status(solution_node):
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.INACTIVE,
        previous_date = datetime.date(day=1, month=1, year=2000),
        due_date = datetime.date(day=1, month=1, year=2001),
        successes = 10,
        failures = 0,
    )
    solution_node.comment = solution_data.make_comment()

    with pytest.raises(ZugSolutionStatusError):    
        ZugTrainingPosition(solution_node)
    
@pytest.mark.parametrize(
    'training_result, expected_queue_position',
    (
        (ZugTrainingPosition.SUCCESS, 3),
        (ZugTrainingPosition.FAILURE, 3),
    )
)
def testZugTrainingPosition_play_new_solution_status(
        solution_node,
        training_result,
        expected_queue_position,
):
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.NEW,
        previous_date = datetime.date(day=1, month=1, year=2000),
        due_date = datetime.date(day=1, month=1, year=2001),
        successes = 10,
        failures = 0,
    )
    solution_node.comment = solution_data.make_comment()
    
    tp = ZugTrainingPosition(solution_node)
    tp._present = mock.MagicMock(return_value=training_result)

    queue_position = tp.play()

    assert queue_position == expected_queue_position
    
    
