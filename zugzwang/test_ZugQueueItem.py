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


def testZugTrainingPosition_play_solution_status_inactive(solution_node):
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
    

def testZugTrainingPosition_play_solution_status_new(
        solution_node,
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
    tp._show_problem = mock.MagicMock()
    tp._show_solution = mock.MagicMock()
    tp._continue_prompt = mock.MagicMock()    
    tp._result_prompt = mock.MagicMock()

    queue_position = tp.play()

    expected_queue_position = 3    
    solution_data.status = ZugSolutionStatuses.LEARNING_STAGE_1
    expected_comment = solution_data.make_comment()

    assert queue_position == 3
    assert solution_node.comment == expected_comment
    
@pytest.mark.parametrize(
    'user_prompt, expected_status, expected_queue_position',
    (
        (True, ZugSolutionStatuses.LEARNING_STAGE_2, 3),
        (False, ZugSolutionStatuses.LEARNING_STAGE_1, 3),
    )
)
def testZugTrainingPosition_play_solution_status_learning_stage_1(
        solution_node,
        user_prompt,
        expected_status,        
        expected_queue_position,
):
    solution_data = ZugSolutionData(
        status = ZugSolutionStatuses.LEARNING_STAGE_1,
        previous_date = datetime.date(day=1, month=1, year=2000),
        due_date = datetime.date(day=1, month=1, year=2001),
        successes = 10,
        failures = 0,
    )
    solution_node.comment = solution_data.make_comment()
    
    tp = ZugTrainingPosition(solution_node)
    tp._show_problem = mock.MagicMock()
    tp._show_solution = mock.MagicMock()
    tp._continue_prompt = mock.MagicMock()    
    tp._result_prompt = mock.MagicMock(return_value=user_prompt)
    
    queue_position = tp.play()

    expected_queue_position = 3
    solution_data.status = expected_status
    expected_comment = solution_data.make_comment()

    assert queue_position == 3
    assert solution_node.comment == expected_comment
    assert queue_position == expected_queue_position
    
    
