from zugzwang.queue import ZugQueue, ZugTrainingPosition
from zugzwang.chapter import ZugChapter
from zugzwang.constants import ZugTrainingStatuses

class ZugTrainer():
    
    def __init__(self, chapter: ZugChapter):
        self._chapter = chapter
        self._queue = ZugQueue()

    def _fill_queue(self):
        pass
        
    def train(self):
        self._fill_queue()
        self._queue.play()
        self._chapter.save()


class ZugPositionTrainer(ZugTrainer):
    
    def _fill_queue(self):
        learning_capacity = self._chapter.root.data.learning_remaining
        for solution in self._chapter.solutions:
            if (not solution.is_learned()) and learning_capacity > 0:
                self._queue.insert(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.NEW)
                )
                learning_capacity -= 1
                continue
            if solution.is_learned() and solution.is_due():
                self._queue.insert(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.REVIEW)
                )
                continue


class ZugLineTrainer():

    def _fill_queue(self):
        for line in _get_lines():
            self._queue.insert(line)

    def _get_lines(self):
        return []
    
        
