import chess
from typing import Optional, List

from zugzwang.game import ZugSolution, ZugSolutionData
from zugzwang.board import ZugBoard
from zugzwang.constants import ZugTrainingStatuses

# TODO (non-critical)
# 1. Decide whether to factor the _present_front() and _present_back() methods into
#    ZugQueueItem as they appear to be identical for both subclasses.
# 2. Decide whether the ZugTrainingPosition and ZugTrainingLine, and hence their
#    presenters too, belong with the training session classes, rather than the queue.
#    I think they probably do.

class ZugQueueItem():
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    QUIT = 'QUIT'

    def play(self) -> Optional[int]:
        return self._interpret_result(self._present())

    def _present(self) -> str:
        return self.SUCCESS

    def _interpret_result(self, result: str) -> Optional[int]:
        if result == self.QUIT:
            return ZugQueue.QUIT        
        if result == self.SUCCESS:
            return self._on_success()
        if result == self.FAILURE:
            return self._on_failure()

    def _on_success(self):
        return ZugQueue.DISCARD

    def _on_failure(self):
        return ZugQueue.REINSERT


class ZugTrainingLine(ZugQueueItem):

    def __init__(self, line: List[chess.pgn.GameNode]):
        self._line = line

    def _present(self):        
        return ZugTrainingLinePresenter(self._line).present()

        
class ZugTrainingLinePresenter():

    def __init__(self, line: List[chess.pgn.GameNode]):
        self._line = line
        self._perspective = line[0].board().turn
    
    def present(self):
        for problem, solution in zip(self._line[::2], self._line[1::2]):
            result = self._present_pair(problem, solution)
            if result != ZugQueueItem.SUCCESS:
                break
        return result

    def _present_pair(self, problem, solution):
        self._present_front(problem)        
        while not self._pause():
            self._present_front(problem)
        result = self._present_back(solution)
        while result is None:
            result = self._present_back(solution)
        return result
        
    def _present_front(self, node):
        board = ZugBoard(node.board()).make_string(self._perspective)
        self._clear_screen()
        self._print_synopsis()
        print(board)
        self._prompt_front()

    def _present_back(self, node):
        board = ZugBoard(node.board()).make_string(self._perspective)
        self._clear_screen()
        print(board)
        self._prompt_back()
        return self._interpret_user_input()

    def _print_synopsis(self):
        print("Your turn\n")

    def _prompt_front(self):
        print("Look at the position, then hit enter to see the solution\n")

    def _prompt_back(self):
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

    @classmethod
    def _interpret_user_input(cls):
        accepted_input = {
            '': ZugQueueItem.SUCCESS,
            'f': ZugQueueItem.FAILURE,
            'q': ZugQueueItem.QUIT,
        }
        return accepted_input.get(cls._get_user_input(), None)
    
    
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
        if self._status == ZugTrainingStatuses.NEW:
            print("NEW : this is a position you haven't seen before\n")
        if self._status in learning_statuses:
            print("LEARNING : this is a position you're currently learning\n")
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

    
class ZugQueue():

    REINSERT = 'REINSERT'
    DISCARD = 'DISCARD'
    QUIT = 'QUIT'

    _REINSERTION_INDEX = 3
    
    def __init__(self):
        self._queue = []

    @property
    def queue(self):
        return self._queue

    def insert(
            self,
            item: ZugQueueItem,
            index: Optional[int]=None
    ):
        if index is not None:
            self._queue.insert(index, item)
        else:
            self._queue.append(item)

    def play(self) -> None:
        while self._queue:
            item = self._queue.pop(0)
            item_directive = item.play()
            if item_directive == self.QUIT:
                break
            if item_directive == self.REINSERT:
                self.insert(item, self._REINSERTION_INDEX)                
            if item_directive == self.DISCARD:
                pass
