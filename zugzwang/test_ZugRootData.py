import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
)

def test_ZugRootData_from_comment():
    comment = 'last_access=01-01-2000;new_remaining=20;new_limit=25'    
    root_data = ZugRootData.from_comment(comment)
    assert root_data.last_access == datetime.date(day=1, month=1, year=2000)
    assert root_data.new_remaining == 20
    assert root_data.new_limit == 25

def test_ZugRootData_make_comment():
    last_access = datetime.date(day=1, month=1, year=2000)
    new_remaining = 10
    new_limit = 10
    root_data = ZugRootData(last_access, new_remaining, new_limit)
    expected_comment = 'last_access=01-01-2000;new_remaining=10;new_limit=10'
    assert root_data.make_comment() == expected_comment
    
