import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugSolutionStatuses,
    ZugSolutionData,
    ZugSolution
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
def solution(solution_data):
    parent = chess.pgn.Game()
    move = chess.Move.from_uci('e2e4')
    node = chess.pgn.ChildNode(parent, move)
    move = chess.Move.from_uci('e7e5')
    node = chess.pgn.ChildNode(node, move)
    node.comment = solution_data.make_comment()
    return ZugSolution(node)


def test_ZugSolutionData_from_comment():
    comment = (
        'status=REVIEW;'
        'previous_date=01-01-2000;'
        'due_date=01-01-2001;'
        'successes=10;'
        'failures=0'
    )
    solution_data = ZugSolutionData.from_comment(comment)
    assert solution_data.status == ZugSolutionStatuses.REVIEW
    assert solution_data.previous_date == datetime.date(day=1, month=1, year=2000)
    assert solution_data.due_date == datetime.date(day=1, month=1, year=2001)
    assert solution_data.successes == 10
    assert solution_data.failures == 0


def test_ZugSolutionData_make_comment(solution_data):
    expected_comment = (
        'status=INACTIVE;'
        'previous_date=01-01-2000;'
        'due_date=01-01-2001;'
        'successes=10;'
        'failures=0'
    )
    assert solution_data.make_comment() == expected_comment
    

def test_ZugSolution_update_game_comment(solution):
    solution.update_node_comment()

    
def test_update_status_counts(solution):
    solution.update_status_counts()

    
def test_update_status_counts(solution):
    solution.reset_data()
