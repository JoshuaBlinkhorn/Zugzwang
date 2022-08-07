import chess
from typing import List

from zugzwang.queue import ZugQueueItem
from zugzwang.board import ZugBoard


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
