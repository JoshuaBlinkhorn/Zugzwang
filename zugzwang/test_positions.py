import pytest
import mock
import chess


from zugzwang.game import ZugRoot, ZugRootData, ZugSolution, ZugSolutionData
from zugzwang.positions import (
    ZugTrainingStatuses,
    ZugTrainingPosition,
    ZugTrainingPositionPresenter,
)
from zugzwang.queue import ZugQueue, ZugQueueItem

@pytest.fixture
def game():
    game = chess.pgn.Game()
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
    return solution_node

@pytest.fixture
def solution(solution_node, root):
    solution = ZugSolution(solution_node, root)
    solution.forgotten = mock.MagicMock()
    solution.learned = mock.MagicMock()
    solution.recalled = mock.MagicMock()
    solution.remembered = mock.MagicMock()    
    return solution


class TestZugTrainingPosition:
    """Unit tests for ZugTrainingPosition."""
    
    @pytest.mark.parametrize(
        (
            'training_status, presentation_result, '
            'expected_training_status, expected_method_name, expected_directive'
        ),
        [
            (
                ZugTrainingStatuses.LEARNING_STAGE_1, ZugQueueItem.FAILURE,
                ZugTrainingStatuses.LEARNING_STAGE_1, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.LEARNING_STAGE_2, ZugQueueItem.FAILURE,
                ZugTrainingStatuses.LEARNING_STAGE_1, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.REMEMBERING_STAGE_1, ZugQueueItem.FAILURE,
                ZugTrainingStatuses.REMEMBERING_STAGE_1, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.REMEMBERING_STAGE_2, ZugQueueItem.FAILURE,
                ZugTrainingStatuses.REMEMBERING_STAGE_1, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.REVIEW, ZugQueueItem.FAILURE,
                ZugTrainingStatuses.REMEMBERING_STAGE_1, 'forgotten', ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.NEW, ZugQueueItem.SUCCESS,
                ZugTrainingStatuses.LEARNING_STAGE_1, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.LEARNING_STAGE_1, ZugQueueItem.SUCCESS,
                ZugTrainingStatuses.LEARNING_STAGE_2, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.LEARNING_STAGE_2, ZugQueueItem.SUCCESS,
                ZugTrainingStatuses.REVIEW, 'learned', ZugQueue.DISCARD
            ),
            (
                ZugTrainingStatuses.REMEMBERING_STAGE_1, ZugQueueItem.SUCCESS,
                ZugTrainingStatuses.REMEMBERING_STAGE_2, None, ZugQueue.REINSERT
            ),
            (
                ZugTrainingStatuses.REMEMBERING_STAGE_2, ZugQueueItem.SUCCESS,
                ZugTrainingStatuses.REVIEW, 'remembered', ZugQueue.DISCARD
            ),
            (
                ZugTrainingStatuses.REVIEW, ZugQueueItem.SUCCESS, 
                ZugTrainingStatuses.REVIEW, 'recalled', ZugQueue.DISCARD
            ),
        ]
    )
    def test_play(
            self,
            solution,
            training_status,            
            presentation_result,
            expected_training_status,
            expected_method_name,
            expected_directive,
    ):
        # We test that the correct return value is given, and the correct side effect
        # takes place. The return value is a ZugQueue class variable. The side effect
        # is calling a method on the solution - or not. We could check that the
        # side effect takes place by assessing directly the state of the solution.
        # But the called methods are already unit tested. So we should think of this
        # test as *defining*, as well as asserting, the desired side effect.
        method_names = ('learned', 'recalled', 'forgotten', 'remembered')
        training_position = ZugTrainingPosition(solution, training_status)
        training_position._present = mock.MagicMock(return_value=presentation_result)

        # Call the function.
        directive = training_position.play()

        # Check the return value and status
        assert directive == expected_directive
        assert training_position.status == expected_training_status
        
        # Check the expected method is called, if there is one.
        if expected_method_name is not None:
            expected_method = getattr(solution, expected_method_name)
            expected_method.asssert_called_once()

        # Check that the other methods aren't called
        for method_name in method_names:
            if method_name != expected_method_name:
                method = getattr(solution, method_name)                
                method.asssert_not_called()


class TestZugTrainingPositionPresenter:
    """Unit tests for ZugTrainingPositionPresenter."""

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
