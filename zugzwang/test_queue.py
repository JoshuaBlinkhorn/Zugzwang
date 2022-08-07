import pytest
import mock

from zugzwang.queue import ZugQueue, ZugQueueItem


class TestZugQueue:
    
    def test_ZuqQueue_play_no_reinsertion(self):
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

    def test_ZuqQueue_play_with_reinsertion(self):
        # calling play() on a three-item queue with reinsertion of each item twice
        # at index 3 (the end of the queue)
        # play() should be called three times on each item, and insert() called
        # twice for each with index 3
        
        q = ZugQueue()
        is_reinsertable_list = [q.REINSERT, q.REINSERT, q.DISCARD]
        
        first_item = ZugQueueItem()
        first_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
        q.insert(first_item)
        
        second_item = ZugQueueItem()
        second_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
        q.insert(second_item)
        
        third_item = ZugQueueItem()
        third_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
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
        
    def test_ZuqQueue_insert(self):
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

        
class TestZugQueueItem:
    @pytest.mark.parametrize(
        'presentation_result, expected_return_value',
        [
            (ZugQueueItem.SUCCESS, ZugQueue.DISCARD),
            (ZugQueueItem.FAILURE, ZugQueue.REINSERT),
            (ZugQueueItem.QUIT, ZugQueue.QUIT),
        ],
    )
    def test_play(self, presentation_result, expected_return_value):
        queue_item = ZugQueueItem()
        queue_item._present = mock.MagicMock(return_value = presentation_result)
        assert queue_item.play() == expected_return_value

