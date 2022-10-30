from zugzwang.queue import ZugQueue
from zugzwang.positions import ZugTrainingPosition, ZugTrainingStatuses
from zugzwang.lines import ZugTrainingLine

# TODO fix this: we need this for typing but it creates a circular import
#from zugzwang.chapter import ZugChapter

class ZugTrainer():
    
    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = ZugQueue()

    def _fill_queue(self):
        pass
        
    def train(self):
        self._fill_queue()
        self._queue.play()


class ZugPositionTrainer(ZugTrainer):
    
    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = ZugQueue(insertion_index=3, insertion_radius=1)

    def _fill_queue(self):
        learning_capacity = self._chapter.root.data.learning_remaining
        for solution in self._chapter.solutions:
            if (not solution.is_learned()) and learning_capacity > 0:
                self._queue.append(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.NEW)
                )
                learning_capacity -= 1
                continue
            if solution.is_learned() and solution.is_due():
                self._queue.append(
                    ZugTrainingPosition(solution, ZugTrainingStatuses.REVIEW)
                )
                continue


class ZugLineTrainer(ZugTrainer):

    def __init__(self, chapter):
        self._chapter = chapter
        self._queue = ZugQueue(insertion_index=3)

    def _fill_queue(self):
        for line in self._get_lines():
            self._queue.append(line)

    def _get_lines(self):
        return [ZugTrainingLine(line) for line in self._chapter.lines]
    

