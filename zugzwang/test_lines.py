import pytest
import mock
import chess

from zugzwang.lines import ZugTrainingLine, ZugTrainingLinePresenter
from zugzwang.queue import ZugQueue, ZugQueueItem

@pytest.fixture
def line():
    root = chess.pgn.Game()
    return [root] * 4

class TestZugTrainingLine:
    @pytest.mark.parametrize(
        'presentation_result, expected_return_value',
        [
            (ZugQueueItem.SUCCESS, ZugQueue.DISCARD),
            (ZugQueueItem.FAILURE, ZugQueue.REINSERT),
            (ZugQueueItem.QUIT, ZugQueue.QUIT),
        ],
    )
    def test_play(self, line, presentation_result, expected_return_value):
        training_line = ZugTrainingLine(line)
        training_line._present = mock.MagicMock(return_value=presentation_result)
        assert training_line.play() == expected_return_value


class TestZugTrainingLinePresenter:

    @pytest.mark.parametrize(
        'user_input, expected_return_value',
        [
            (('','','',''), ZugQueueItem.SUCCESS),
            (('az','','bcty','a','','tt','aq','','as', '213', ''), ZugQueueItem.SUCCESS),
            (('\n','','\n','','\n\n','','\n\n\n',''), ZugQueueItem.SUCCESS),
            (('','q'), ZugQueueItem.QUIT),
            (('','','','q'), ZugQueueItem.QUIT),            
            (('q','','','q','q','',''), ZugQueueItem.SUCCESS),            
            (('','f'), ZugQueueItem.FAILURE),
            (('','','','f'), ZugQueueItem.FAILURE),            
            (('f','','','f','f','',''), ZugQueueItem.SUCCESS),            
        ],
        ids = [
            'perfect input',
            'imperfect input',
            'line breaks ignored',
            'quit request delivered on first solution',
            'quit request delivered on second solution',            
            'early quit requests ignored',
            'failure verdict delivered on first solution',
            'failure verdict delivered on second solution',            
            'early failure verdicts ignored',
        ]
    )
    def test_present(
            self,
            line,
            user_input,
            expected_return_value
    ):
        ZugTrainingLinePresenter._get_user_input = mock.MagicMock(
            side_effect=user_input
        )
        presenter = ZugTrainingLinePresenter(line)
        assert presenter.present() == expected_return_value
