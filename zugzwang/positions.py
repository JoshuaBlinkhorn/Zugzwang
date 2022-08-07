import chess

from zugzwang.queue import ZugQueue, ZugQueueItem
from zugzwang.game import ZugSolution
from zugzwang.board import ZugBoard


class ZugTrainingStatuses():
    NEW = 'NEW'
    LEARNING_STAGE_1 = 'LEARNING_STAGE_1'
    LEARNING_STAGE_2 = 'LEARNING_STAGE_2'
    REMEMBERING_STAGE_1 = 'REMEMBERING_STAGE_1'
    REMEMBERING_STAGE_2 = 'REMEMBERING_STAGE_2'
    REVIEW = 'REVIEW'


class ZugTrainingPosition(ZugQueueItem):

    def __init__(self, solution: ZugSolution, status: str):
        self._solution = solution
        self._status = status

    @property
    def solution(self):
        return self._solution
        
    @property
    def status(self):
        return self._status
        
    def _present(self) -> int:
        presenter = ZugTrainingPositionPresenter(self._solution.node, self._status)
        return presenter.present()

    def _on_success(self):
        statuses = {
            ZugTrainingStatuses.NEW: ZugTrainingStatuses.LEARNING_STAGE_1,
            ZugTrainingStatuses.LEARNING_STAGE_1: ZugTrainingStatuses.LEARNING_STAGE_2,
            ZugTrainingStatuses.LEARNING_STAGE_2: ZugTrainingStatuses.REVIEW,
            ZugTrainingStatuses.REMEMBERING_STAGE_1: ZugTrainingStatuses.REMEMBERING_STAGE_2,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: ZugTrainingStatuses.REVIEW,
            ZugTrainingStatuses.REVIEW: ZugTrainingStatuses.REVIEW,             
        }
        actions = {
            ZugTrainingStatuses.NEW: lambda: None,
            ZugTrainingStatuses.LEARNING_STAGE_1: lambda: None,
            ZugTrainingStatuses.LEARNING_STAGE_2: self._solution.learned,
            ZugTrainingStatuses.REMEMBERING_STAGE_1: lambda: None,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: self._solution.remembered,
            ZugTrainingStatuses.REVIEW: self._solution.recalled,  
        }
        directives = {
            ZugTrainingStatuses.NEW: ZugQueue.REINSERT,
            ZugTrainingStatuses.LEARNING_STAGE_1: ZugQueue.REINSERT,
            ZugTrainingStatuses.LEARNING_STAGE_2: ZugQueue.DISCARD, 
            ZugTrainingStatuses.REMEMBERING_STAGE_1: ZugQueue.REINSERT,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: ZugQueue.DISCARD,
            ZugTrainingStatuses.REVIEW: ZugQueue.DISCARD, 
        }
        # The action and directive depend on the current status.
        # So perform the action and set the directive *before* updating the status.
        actions.get(self._status).__call__()
        directive = directives.get(self._status)
        self._status = statuses.get(self._status)
        return directive

    def _on_failure(self):
        statuses = {
            ZugTrainingStatuses.LEARNING_STAGE_1: ZugTrainingStatuses.LEARNING_STAGE_1,
            ZugTrainingStatuses.LEARNING_STAGE_2: ZugTrainingStatuses.LEARNING_STAGE_1,
            ZugTrainingStatuses.REMEMBERING_STAGE_1: ZugTrainingStatuses.REMEMBERING_STAGE_1,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: ZugTrainingStatuses.REMEMBERING_STAGE_1,
            ZugTrainingStatuses.REVIEW: ZugTrainingStatuses.REMEMBERING_STAGE_1,
        }
        directives = {
            ZugTrainingStatuses.LEARNING_STAGE_1: ZugQueue.REINSERT,
            ZugTrainingStatuses.LEARNING_STAGE_2: ZugQueue.REINSERT,
            ZugTrainingStatuses.REMEMBERING_STAGE_1: ZugQueue.REINSERT,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: ZugQueue.REINSERT,
            ZugTrainingStatuses.REVIEW: ZugQueue.REINSERT,
        }
        actions = {
            ZugTrainingStatuses.LEARNING_STAGE_1: lambda: None,
            ZugTrainingStatuses.LEARNING_STAGE_2: lambda: None,
            ZugTrainingStatuses.REMEMBERING_STAGE_1: lambda: None,
            ZugTrainingStatuses.REMEMBERING_STAGE_2: lambda: None,
            ZugTrainingStatuses.REVIEW: self._solution.forgotten,
        }
        # The action and directive depend on the current status.
        # So perform the action and set the directive *before* updating the status.
        actions.get(self._status).__call__()
        directive = directives.get(self._status)
        self._status = statuses.get(self._status)
        return directive


class ZugTrainingPositionPresenter():

    def __init__(
            self,
            solution_node: chess.pgn.ChildNode,
            status: str,
    ):
        self._status = status
        self._front = ZugBoard(solution_node.parent.board())
        self._back = ZugBoard(solution_node.board())
        self._perspective = solution_node.parent.board().turn
        
    def present(self):
        self._present_front()
        while not self._pause():
            self._present_front()
        result = self._present_back()
        while result is None:
            result = self._present_back()
        return result

    def _present_front(self):
        board = self._front.make_string(self._perspective)
        self._clear_screen()        
        self._print_synopsis()
        print(board)
        self._prompt_front()

    def _present_back(self):
        board = self._back.make_string(self._perspective)
        self._clear_screen()
        print(board)
        self._prompt_back()
        return self._interpret_user_input()

    def _interpret_user_input(self):
        if self._status == ZugTrainingStatuses.NEW:
            accepted_input = {
                '': ZugQueueItem.SUCCESS,
                'q': ZugQueueItem.QUIT,
            }
        else:
            accepted_input = {
                '': ZugQueueItem.SUCCESS,
                'f': ZugQueueItem.FAILURE,
                'q': ZugQueueItem.QUIT,                
            }
        return accepted_input.get(self._get_user_input(), None)

    def _print_synopsis(self):
        learning_statuses = (
            ZugTrainingStatuses.LEARNING_STAGE_1,            
            ZugTrainingStatuses.LEARNING_STAGE_2,
        )
        remembering_statuses = (
            ZugTrainingStatuses.REMEMBERING_STAGE_1,            
            ZugTrainingStatuses.REMEMBERING_STAGE_2,
        )
        if self._status == ZugTrainingStatuses.NEW:
            print("NEW : this is a position you haven't seen before\n")
        if self._status in learning_statuses:
            print("LEARNING : this is a position you're currently learning\n")
        if self._status in remembering_statuses:
            print("REMEMBERING : this is a position you're currently remembering\n")
        if self._status == ZugTrainingStatuses.REVIEW:
            print("RECALL : this is a position you've learned, due for recall\n")

    def _prompt_front(self):
        if self._status == ZugTrainingStatuses.NEW:
            print("Look at the position, then hit enter to see the solution\n")
        else:
            print("Recall the move if you can, then hit enter\n")

    def _prompt_back(self):
        if self._status == ZugTrainingStatuses.NEW:
            print("Hit enter to continue\n")
        else:
            print("Hit enter for success, 'f' for failure\n")

    @classmethod
    def _clear_screen(cls):
        print('\n' * 100)
    
    @classmethod
    def _get_user_input(cls):
        return input(':')

    @classmethod
    def _pause(cls):
        return cls._get_user_input() == ''
