import pytest
import mock

from zugzwang.queue import ZugQueue, ZugQueueItem


class TestZugQueue:
    """Unit tests for the ZugQueue class."""
    
    def test_play_no_reinsertion(self):
        """
        Calling play() on a three-itme queue with no reinsertion.
        play() is called on each item, and nothing is reinserted.
        """
        # calling play() on a three item queue with no reinsertion
        # the queue should call play on each item
        # and q.insert should not be called at all
        
        queue = ZugQueue()

        first_item = ZugQueueItem()
        first_item.play = mock.MagicMock(return_value=None)
        queue.insert(first_item)
        
        second_item = ZugQueueItem()
        second_item.play = mock.MagicMock(return_value=None)
        queue.insert(second_item)
        
        third_item = ZugQueueItem()
        third_item.play = mock.MagicMock(return_value=None)
        queue.insert(third_item)
        
        queue.insert = mock.MagicMock()            
        expected_insert_calls = []
        
        queue.play()
        
        assert queue.length() == 0
        assert first_item.play.mock_calls == [mock.call()]
        assert second_item.play.mock_calls == [mock.call()]
        assert third_item.play.mock_calls == [mock.call()]
        assert queue.insert.mock_calls == expected_insert_calls    

    def test_ZuqQueue_play_with_reinsertion(self):
        """
        Calling play() on a three-item queue with each item being reinserted twice.
        play() is called three times on each item, and each is reinserted twice.
        """
        
        queue = ZugQueue(insertion_index=3)
        is_reinsertable_list = [queue.REINSERT, queue.REINSERT, queue.DISCARD]
        
        first_item = ZugQueueItem()
        first_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
        queue.insert(first_item)
        
        second_item = ZugQueueItem()
        second_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
        queue.insert(second_item)
        
        third_item = ZugQueueItem()
        third_item.play = mock.MagicMock(side_effect = is_reinsertable_list)
        queue.insert(third_item)
        
        queue.insert = mock.MagicMock(side_effect=queue.insert)    
        expected_insert_calls = [
            mock.call(first_item, 3),
            mock.call(second_item, 3),
            mock.call(third_item, 3),
            mock.call(first_item, 3),
            mock.call(second_item, 3),
            mock.call(third_item, 3),
        ]
        
        queue.play()
        
        assert queue.length() == 0
        assert first_item.play.mock_calls == [mock.call()] * 3
        assert second_item.play.mock_calls == [mock.call()] * 3
        assert third_item.play.mock_calls == [mock.call()] * 3
        assert queue.insert.mock_calls == expected_insert_calls

    @pytest.mark.parametrize(
        'insertion_index',
        list(range(10))
    )
    def test_insert(self, insertion_index):
        """
        Items inserted without an index go at the reinsertion index, or at the
        back of the queue if the index is out of range. 
        """

        items = [ZugQueueItem() for _ in range(10)]
        expected_items = []
        
        queue = ZugQueue(insertion_index=insertion_index)        
        assert queue.items == expected_items

        for i in range(0,10):
            expected_items.insert(insertion_index, items[i])            
            queue.insert(items[i])
            assert queue.items == expected_items


    @pytest.mark.parametrize(
        'insertion_index',
        list(range(10))
    )
    def test_insert_with_index(self, insertion_index):
        """
        Items inserted with an index go in at that index, or at the back of the 
        queue if that index is out of range. 
        """
        
        items = [ZugQueueItem() for _ in range(10)]
        expected_items = []
        
        queue = ZugQueue()        
        assert queue.items == expected_items

        for i in range(0,10):
            expected_items.insert(insertion_index, items[i])            
            queue.insert(items[i], index=insertion_index)
            assert queue.items == expected_items


    @pytest.mark.parametrize(
        'insertion_radius',
        list(range(11))
    )
    def test_insert_with_radius(self, insertion_radius):
        """
        Items inserted with a radius r, but no explicit index, enter the queue at 
        some index i which has distance at most r from the default insertion index.

        Moreover, the distribution is uniform accross the allowed range, such that
        every possible entry index is observed over sufficiently many repetitions.
        Here we consider 1000 repetitions sufficiently many for a radius of at most
        10.
        """
        num_repetitions = 1000
        queues = []
        items = [ZugQueueItem() for _ in range(100)]
        inserted_item = ZugQueueItem()        

        for repetition in range(num_repetitions):
            queue = ZugQueue(insertion_index=50)
            queues.append(queue)
            for item in items:
                queue.insert(item)

            queue.insert(inserted_item, radius=insertion_radius)                
        
            item_range = queue.items[50-insertion_radius:50+insertion_radius+1]        
            assert inserted_item in item_range

        assert len(queues) == num_repetitions
        for i in range(50-insertion_radius, 50+insertion_radius+1):
            assert any(
                queue.items[i] == inserted_item
                for queue in queues
            )


    def test_ZuqQueue_insert_default(self):
        """
        The default queue should insert at the front.
        """

        items = [ZugQueueItem() for _ in range(3)]
        
        queue = ZugQueue()
        assert queue.items == []
        
        queue.insert(items[0])
        assert queue.items == [items[0]]
        
        queue.insert(items[1])
        assert queue.items == [items[1], items[0]]
        
        queue.insert(items[2])
        assert queue.items == [items[2], items[1], items[0]]

        
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

