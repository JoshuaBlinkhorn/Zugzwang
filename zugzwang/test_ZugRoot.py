import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
    ZugRoot
)

LAST_ACCESS = datetime.date(day=1, month=1, year=2000)
NEW_REMAINING = 20
NEW_LIMIT = 25
NEW = 10
REVIEW = 100
INACTIVE = 20
REACHABLE = 150

@pytest.fixture
def root():
    root_data = ZugRootData(
        LAST_ACCESS,
        NEW_REMAINING,
        NEW_LIMIT,
        NEW,
        REVIEW,
        INACTIVE,
        REACHABLE
    )
    game = chess.pgn.Game()
    game.comment = root_data.make_comment()
    return ZugRoot(game)
    

def test_ZugRoot_init(root):
    assert root.data.last_access == LAST_ACCESS
    assert root.data.new_remaining == NEW_REMAINING
    assert root.data.new_limit == NEW_LIMIT
    assert root.data.new == NEW
    assert root.data.review == REVIEW
    assert root.data.inactive == INACTIVE
    assert root.data.reachable == REACHABLE


def test_ZugRoot_update_game_comment(root):
    root.data.last_access = datetime.date(day=1, month=1, year=2001)
    root.data.new_remaining = 0
    root.data.new_limit = 5
    root.data.new = 0
    root.data.review = 110
    root.data.inactive = 25
    root.data.reachable = 155
    root.update_game_comment()
    expected_comment = (
        'last_access=01-01-2001;'
        'new_remaining=0;'
        'new_limit=5;'
        'new=0;'
        'review=110;'
        'inactive=25;'
        'reachable=155'
        )
    assert root.game.comment == expected_comment

    
def test_update_status_counts(root):
    root.update_status_counts()

    
def test_update_status_counts(root):
    root.reset_data()
