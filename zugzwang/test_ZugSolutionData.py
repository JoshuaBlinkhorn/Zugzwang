import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugSolutionData,
    ZugSolutionStatuses,
)

def test_ZugSolutionData_from_comment():
    comment = (
        'status=REVIEW;'
        'previous_date=01-01-2000;'
        'due_date=01-01-2002;'
        'successes=10;'
        'failures=0'
    )
    solution_data = ZugSolutionData.from_comment(comment)
    assert solution_data.status == ZugSolutionStatuses.REVIEW
    assert solution_data.previous_date == datetime.date(day=1, month=1, year=2000)
    assert solution_data.due_date == datetime.date(day=1, month=1, year=2002)
    assert solution_data.successes == 10
    assert solution_data.failures == 0

def test_ZugSolutionData_make_comment():
    status = ZugSolutionStatuses.INACTIVE
    previous_date = datetime.date(day=1, month=1, year=2000)
    due_date = datetime.date(day=1, month=1, year=2002)
    successes = 10
    failures = 0
    solution_data = ZugSolutionData(status, previous_date, due_date, successes, failures)
    expected_comment = (
        'status=INACTIVE;'
        'previous_date=01-01-2000;'
        'due_date=01-01-2002;'
        'successes=10;'
        'failures=0'
    )
    assert solution_data.make_comment() == expected_comment
    
