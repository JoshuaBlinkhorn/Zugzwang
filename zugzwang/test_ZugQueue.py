import pytest
import unittest
import mock

from zugzwang import (
    ZugQueue,
    ZugQueueItem,
)

def test_ZuqQueue_play_no_reinsertion():
    # calling play() on a three item queue with no reinsertion
    # the queue should call play on each item
    # and q.insert should not be called at all

    q = ZugQueue()

    first_item = ZugQueueItem()
    first_item.play = mock.MagicMock(return_value=None)
    q.insert(first_item)

    second_item = ZugQueueItem()
    second_item.play = mock.MagicMock(return_value=None)
    q.insert(second_item)

    third_item = ZugQueueItem()
    third_item.play = mock.MagicMock(return_value=None)
    q.insert(third_item)

    q.insert = mock.MagicMock(side_effect=q.insert)    
    expected_insert_calls = []

    q.play()
    
    assert len(q.queue) == 0
    assert first_item.play.mock_calls == [mock.call()]
    assert second_item.play.mock_calls == [mock.call()]
    assert third_item.play.mock_calls == [mock.call()]
    assert q.insert.mock_calls == expected_insert_calls    

def test_ZuqQueue_play_with_reinsertion():
    # calling play() on a three-item queue with reinsertion of each item twice
    # at index 3 (the end of the queue)
    # play() should be called three times on each item, and insert() called
    # twice for each with index 3

    q = ZugQueue()

    first_item = ZugQueueItem()
    first_item.play = mock.MagicMock(side_effect = [3,3,None])
    q.insert(first_item)

    second_item = ZugQueueItem()
    second_item.play = mock.MagicMock(side_effect = [3,3,None])
    q.insert(second_item)

    third_item = ZugQueueItem()
    third_item.play = mock.MagicMock(side_effect = [3,3,None])
    q.insert(third_item)

    q.insert = mock.MagicMock(side_effect=q.insert)    
    expected_insert_calls = [
        mock.call(first_item, 3),
        mock.call(second_item, 3),
        mock.call(third_item, 3),
        mock.call(first_item, 3),
        mock.call(second_item, 3),
        mock.call(third_item, 3),
    ]

    q.play()
    
    assert len(q.queue) == 0
    assert first_item.play.mock_calls == [mock.call()] * 3
    assert second_item.play.mock_calls == [mock.call()] * 3
    assert third_item.play.mock_calls == [mock.call()] * 3
    assert q.insert.mock_calls == expected_insert_calls
    
def test_ZuqQueue_insert():
    # items inserted without an index go to the front of the queue
    q = ZugQueue()
    assert q.queue == []

    first_item = ZugQueueItem()
    q.insert(first_item)
    assert q.queue == [first_item]
    
    second_item = ZugQueueItem()
    q.insert(second_item)
    assert q.queue == [first_item, second_item]

    # items are inserted at an index when it is given
    middle_item = ZugQueueItem()
    q.insert(middle_item, 1)
    assert q.queue == [first_item, middle_item, second_item]
    


