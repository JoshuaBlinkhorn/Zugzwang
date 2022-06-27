import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
    ZugRoot
)


@pytest.fixture
def root_data():
    return ZugRootData(
        last_access = datetime.date(day=1, month=1, year=2000),
        new_remaining = 20,
        new_limit = 50,
        new = 100,
        review = 150,
        inactive = 50,
        reachable = 250
    )

@pytest.fixture
def root(root_data):
    game = chess.pgn.Game()
    game.comment = root_data.make_comment()
    return ZugRoot(game)


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


def test_ZugRootData_make_comment(root_data):
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


def test_ZugRoot_update_game_comment(root):
    root.update_game_comment


def test_update_status_counts(root):
    root.update_status_counts()

    
def test_update_reset_data(root):
    root.reset_data()
