import pytest
import chess
import mock

from zugzwang.game import (
    ZugSolutionData,
    ZugRootData,
    ZugSolution,
    ZugRoot
)
from zugzwang.constants import ZugTrainingStatuses
from zugzwang.queue import (
    ZugQueue,
    ZugQueueItem,
    ZugTrainingPositionPresenter,
    ZugTrainingLinePresenter,
    ZugTrainingPosition
)

# TODO (non-critical):
# 1 - can we remove the dependency on mock, use pytest monkeypatch instead?

@pytest.fixture
def game():
    game = chess.pgn.Game()
    game.comment = ZugRootData().make_json()
    return game

@pytest.fixture
def root(game):
    return ZugRoot(game)

@pytest.fixture
def solution_node(game):
    move = chess.Move.from_uci('e2e4')
    problem_node = chess.pgn.ChildNode(game, move)
    move = chess.Move.from_uci('e7e5')
    solution_node = chess.pgn.ChildNode(problem_node, move)
    solution_node.comment = ZugSolutionData().make_json()    
    return solution_node

@pytest.fixture
def solution(solution_node, root):
    solution = ZugSolution(solution_node, root)
    solution.forgotten = mock.MagicMock()
    solution.learned = mock.MagicMock()
    solution.recalled = mock.MagicMock()
    return solution
    
@pytest.fixture
def line():
    root = chess.pgn.Game()
    return [root] * 4

class TestZugTrainingPositionPresenter:

    @pytest.mark.parametrize(
        'user_input, expected_return_value',
        [
            (('',''), ZugQueueItem.SUCCESS),
            (('azby','bcty','asfhwrqreqrw','','assirtt','aq',''), ZugQueueItem.SUCCESS),
            (('azby','f','asfhwas,','','assirtt','f','h',''), ZugQueueItem.SUCCESS),
            (('\n','','\n',''), ZugQueueItem.SUCCESS),
            (('','q'), ZugQueueItem.QUIT),
            (('q','',''), ZugQueueItem.SUCCESS),            
        ],
        ids = [
            'perfect input',
            'imperfect input',
            'failure verdict ignored throughout',
            'line breaks ignored',
            'quit request delivered',
            'premature quit request ignored',
        ]
    )
    def test_present_new(
            self,
            solution_node,
            user_input,
            expected_return_value
    ):
        ZugTrainingPositionPresenter._get_user_input = mock.MagicMock(
            side_effect=user_input
        )
        presenter = ZugTrainingPositionPresenter(
            solution_node,
            status=ZugTrainingStatuses.NEW
        )
        assert presenter.present() == expected_return_value

    @pytest.mark.parametrize(
        'status',
        [
            ZugTrainingStatuses.LEARNING_STAGE_1,
            ZugTrainingStatuses.LEARNING_STAGE_2,
            ZugTrainingStatuses.REVIEW,                        
        ]
    )
    @pytest.mark.parametrize(
        'user_input, expected_return_value',
        [
            (('\n','','\n',''), ZugQueueItem.SUCCESS),
            (('',''), ZugQueueItem.SUCCESS),
            (('q749gb','sd','','asggnrpgnpir',''), ZugQueueItem.SUCCESS),
            (('','f'), ZugQueueItem.FAILURE),
            (('azby','bcty','qreqrw','','assirtt','aq','f'), ZugQueueItem.FAILURE),
            (('','q'), ZugQueueItem.QUIT),
            (('q','',''), ZugQueueItem.SUCCESS),
            (('f','',''), ZugQueueItem.SUCCESS),                        
        ],
        ids = [
            'line breaks',
            'perfect input, success',
            'imperfect input, success',
            'perfect input, failure',
            'imperfect input, failure',
            'quit request delivered',
            'premature quit request ignored',                        
            'premature failure verdict ignored',            
        ]
    )
    def test_present_non_new(
            self,
            solution_node,
            user_input,
            expected_return_value,
            status,
    ):
        ZugTrainingPositionPresenter._get_user_input = mock.MagicMock(
            side_effect=user_input
        )
        presenter = ZugTrainingPositionPresenter(
            solution_node,
            status=status,
        )
        assert presenter.present() == expected_return_value

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


class TestZugQueueItem:
    @pytest.mark.parametrize(
        'presentation_result, expected_return_value',
        [
            (ZugQueueItem.SUCCESS, ZugQueue.DISCARD),
            (ZugQueueItem.FAILURE, ZugQueue.REINSERT),
            (ZugQueueItem.QUIT, ZugQueue.QUIT),
        ],
    )
    def test_play(self, presentation_result, expected_return_value, monkeypatch):

        def mock_present(*args, **kwargs):
            return presentation_result
        monkeypatch.setattr(ZugQueueItem, '_present', mock_present)
        
        assert ZugQueueItem().play() == expected_return_value

class TestZugTrainingPosition:
    def test_play_review_phase_failure(self, solution, training_status):
        training_position = ZugTrainingPosition(
            solution,
            ZugTrainingStatuses.REVIEW,            
        )
        training_position._present = mock.MagicMock(
            return_value = ZugQueueItem.FAILURE
        )

        directive = training_position.play()
        
        assert directive == ZugQueue.REINSERT
        solution.forgotten.asssert_called_once()
        solution.learned.asssert_not_called()
        solution.recalled.asssert_not_called()        
