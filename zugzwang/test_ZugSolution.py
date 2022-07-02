import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugSolutionStatuses,
    ZugSolutionData,
    ZugSolution
)

# dates here are relative to a fixed today
# as we want check how that date is written into another format, it is
# best to use an explicit date whose representation in the new format is known
TODAY = datetime.date(day=1, month=1, year=2000)
YESTERDAY = TODAY - datetime.timedelta(days=1)
TOMORROW = TODAY + datetime.timedelta(days=1)
PAST_EPOCH = TODAY - datetime.timedelta(days=1000)
FUTURE_EPOCH = TODAY + datetime.timedelta(days=1000)

SUCCESSES = 5
FAILURES = 5

@pytest.fixture
def solution_data():
    return ZugSolutionData(
        status = ZugSolutionStatuses.REVIEW,
        last_study_date = YESTERDAY,
        due_date = TODAY,
        successes = SUCCESSES,
        failures = FAILURES,
    )

@pytest.fixture
def comment():
    return (
        'status=REVIEW;'
        'last_study_date=31-12-1999;'
        'due_date=01-01-2000;'
        'successes=5;'
        'failures=5'
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

def test_ZugSolutionData_from_comment(comment):
    solution_data = ZugSolutionData.from_comment(comment)
    assert solution_data.status == ZugSolutionStatuses.REVIEW
    assert solution_data.last_study_date == YESTERDAY
    assert solution_data.due_date == TODAY
    assert solution_data.successes == SUCCESSES
    assert solution_data.failures == FAILURES


def test_ZugSolutionData_make_comment(solution_data, comment):
    assert solution_data.make_comment() == comment
    

def test_ZugSolutionData_update(solution_data):
    # supplied changes cover all fields
    # the 'successes' value does not differ from the original
    changes = {
        'status': ZugSolutionStatuses.LEARNING_STAGE_1,
        'last_study_date': TODAY,        
        'due_date': TOMORROW,
        'successes': SUCCESSES,
        'failures': FAILURES + 1,                
    }
    solution_data.update(changes)

    assert solution_data.status == ZugSolutionStatuses.LEARNING_STAGE_1
    assert solution_data.last_study_date == TODAY
    assert solution_data.due_date == TOMORROW
    assert solution_data.successes == SUCCESSES
    assert solution_data.failures == FAILURES + 1
    
def test_ZugSolution_update_game_comment(solution):
    solution.update_node_comment()

    
def test_update_status_counts(solution):
    solution.update_status_counts()

    
def test_update_status_counts(solution):
    solution.reset_data()
