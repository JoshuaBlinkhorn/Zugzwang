import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
)

def test_ZugRootData_from_comment():
    comment = (
        'last_access=01-01-2000;'
        'new_remaining=20;'
        'new_limit=25;'
        'new=100;'
        'review=150;'
        'inactive=50;'
        'reachable=250'
    )
    root_data = ZugRootData.from_comment(comment)
    assert root_data.last_access == datetime.date(day=1, month=1, year=2000)
    assert root_data.new_remaining == 20
    assert root_data.new_limit == 25
    assert root_data.new == 100
    assert root_data.review == 150
    assert root_data.inactive == 50
    assert root_data.reachable == 250

def test_ZugRootData_make_comment():
    root_data = ZugRootData(
        last_access = datetime.date(day=1, month=1, year=2000),
        new_remaining = 20,
        new_limit = 50,
        new = 100,
        review = 150,
        inactive = 50,
        reachable = 250
    )
    expected_comment = (
        'last_access=01-01-2000;'
        'new_remaining=20;'
        'new_limit=50;'
        'new=100;'
        'review=150;'
        'inactive=50;'
        'reachable=250'
    )
    assert root_data.make_comment() == expected_comment
    
