import chess
from typing import Optional

from zugzwang.game import ZugSolution, ZugSolutionData
from zugzwang.board import ZugBoard
from zugzwang.constants import ZugTrainingStatuses

class ZugQueueItem():

    def play(self) -> Optional[int]:
        return self._interpret_result(self._present())

    def _present(self) -> str:
        pass

    def _interpret_result(self, result: str) -> Optional[int]:
        pass


class ZugTrainingPosition(ZugQueueItem):

    # return values for public method .play()
    REINSERT = True
    DISCARD = False

    def __init__(self, solution: ZugSolution, status: str):
        self._solution = solution
        self._status = status

    @property
    def solution(self):
        return self._solution
        
    def _present(self):
        presenter = ZugTrainingPositionPresenter(
            self._solution.node,            
            self._status
        )
        return presenter.present()
            
    def _interpret_result(self, result):
        if (self._status == ZugTrainingStatuses.NEW and
            result == ZugTrainingPositionPresenter.SUCCESS):
            self._status = ZugTrainingStatuses.LEARNING_STAGE_1
            return ZugQueue.REINSERT
        if (self._status ==ZugTrainingStatuses.LEARNING_STAGE_1 and
            result == ZugTrainingPositionPresenter.SUCCESS):
            self._status = ZugTrainingStatuses.LEARNING_STAGE_2
            return ZugQueue.REINSERT
        if (self._status == ZugTrainingStatuses.LEARNING_STAGE_1 and
            result == ZugTrainingPositionPresenter.FAILURE):
            self._status = ZugTrainingStatuses.LEARNING_STAGE_1
            return ZugQueue.REINSERT
        if (self._status == ZugTrainingStatuses.LEARNING_STAGE_2 and
            result == ZugTrainingPositionPresenter.SUCCESS):
            self._solution.learned()
            return ZugQueue.DISCARD
        if (self._status == ZugTrainingStatuses.LEARNING_STAGE_2 and
            result == ZugTrainingPositionPresenter.FAILURE):
            self._status = ZugTrainingStatuses.LEARNING_STAGE_1
            return ZugQueue.REINSERT
        if (self._status == ZugTrainingStatuses.REVIEW and
            result == ZugTrainingPositionPresenter.FAILURE):
            self._status = ZugTrainingStatuses.LEARNING_STAGE_1
            self._solution.forgotten()
            return ZugQueue.REINSERT
        if (self._status == ZugTrainingStatuses.REVIEW and
            result == ZugTrainingPositionPresenter.SUCCESS):
            self._solution.recalled()
            return ZugQueue.DISCARD


class ZugTrainingPositionPresenter():

    SUCCESS = True
    FAILURE = False

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
            accepted_input = {'': self.SUCCESS}
        else:
            accepted_input = {'': self.SUCCESS, 'h': self.FAILURE}
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
            print("Hit enter for success, 'h' for failure\n")

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

    REINSERT = True
    DISCARD = False

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
            if item.play() == self.REINSERT:
                self.insert(item, self._REINSERTION_INDEX)



