import pytest
import datetime
import chess.pgn

from zugzwang import (
    ZugRootData,
    ZugRoot
)

def test_ZugRoot_init():
    
    last_access = datetime.date(day=1, month=1, year=2000)
    new_remaining = 20
    new_limit = 25
    root_data = ZugRootData(last_access, new_remaining, new_limit)

    game = chess.pgn.Game()
    game.comment = root_data.make_comment()

    root = ZugRoot(game)

    assert root.last_access == last_access
    assert root.new_remaining == new_remaining
    assert root.new_limit == new_limit


def test_ZugRoot_update_comment():
    
    last_access = datetime.date(day=1, month=1, year=2000)
    new_remaining = 20
    new_limit = 25
    root_data = ZugRootData(last_access, new_remaining, new_limit)

    game = chess.pgn.Game()
    game.comment = root_data.make_comment()

    root = ZugRoot(game)

    root.last_access = datetime.date(day=1, month=1, year=2001)
    root.new_remaining = 0
    root.new_limit = 5

    root.update_game_comment()
    
    expected_comment = 'last_access=01-01-2001;new_remaining=0;new_limit=5'    
    assert root.game.comment == expected_comment
    
    
