import datetime

from constants import ZugColour


class ZugDefaults():
    LEARNING_REMAINING = 10
    LEARNING_LIMIT = 10


class ZugSolutionStatus():
    LEARNED = 'LEARNED'
    UNLEARNED = 'UNLEARNED'


class ZugRootData():

    def __init__(
            self,
            perspective: bool = ZugColour.WHITE,
            last_access: datetime.date = ZugDates.today(),
            learning_remaining: int = ZugDefaults.LEARNING_REMAINING,
            learning_limit: int = ZugDefaults.NEW_LIMIT,
            recall_radius: float = 3.0,
            recall_factor: float = 2.0,
    ):
        self.perspective = perspective
        self.last_access = last_access
        self.learning_remaining = learning_remaining
        self.learning_limit = learning_limit
        self.recall_radius = recall_radius
        self.recall_factor = recall_factor

    @classmethod
    def from_comment(cls, comment: str):
        data = comment.split(';')
        perspective = data[0].split('=')[1]
        perspective = True if perspective == 'WHITE' else False
        last_access = data[1].split('=')[1]
        last_access = datetime.datetime.strptime(last_access, '%d-%m-%Y').date()
        learning_remaining = int(data[2].split('=')[1])
        learning_limit = int(data[3].split('=')[1])
        recall_radius = float(data[4].split('=')[1])
        recall_factor = float(data[5].split('=')[1])
        return ZugRootData(
            perspective,
            last_access,
            learning_remaining,
            learning_limit,
            recall_radius,
            recall_factor,
        )

    def make_comment(self) -> str:
        perspective = 'WHITE' if self.perspective == ZugColour.WHITE  else 'BLACK'
        return ';'.join(
            (
                f'perspective={perspective}',                
                f'last_access={self.last_access.strftime("%d-%m-%Y")}',
                f'learning_remaining={self.learning_remaining}',
                f'learning_limit={self.learning_limit}',
                f'recall_radius={self.recall_radius}',
                f'recall_factor={self.recall_factor}',
            )
        )


class ZugRoot():

    def __init__(self, game: chess.pgn.Game):
        self._data = ZugRootData.from_comment(game.comment)
        self._game = game

    def _reset_solution_data(self):
        solution_data = ZugSolutionData()
        for solution in root.solution_nodes():
            solution.comment = solution_data.make_comment()                

    @classmethod
    def from_naked_game(cls, game):
        game.comment = ZugRootData().make_comment()
        root = ZugRoot(game)
        root._reset_solution_data()
        return root

    @property
    def learning_remaining(self):
        return self._data.learning_remaining
    
    @property
    def recall_radius(self):
        return self._data.recall_radius
    
    @property
    def recall_factor(self):
        return self._data.recall_factor
    
    def reset_training_data(self):
        new_data = ZugSolutionData(
            perspective=self._data.perspective,
        )
        self._reset_solution_data()

    def decrement_learning_remaining(self):
        self._data.learning_remaining -= 1

    def has_new_capacity(self):
        return self._data.learning_remaining > 0

    def update_game_comment(self):
        self._game.comment = self.data.make_comment()

    def update_learning_remaining(self):
        if self._data.last_access < ZugDates.today():
            self._data.learning_remaining = self._data.learning_limit

    def solution_nodes(self) -> List[chess.pgn.ChildNode]:
        # define a list to store solutions and a recursive search function
        solutions = []
        def search_node(
                node: chess.pgn.ChildNode,
                solution_perspective: bool
        ):
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution
                # add it to the set and work recursively on all children
                if node != self._game:
                    solutions.append(node)
                for problem in node.variations:
                    search_node(problem, solution_perspective)                
            else:
                # the node is a problem
                # if it has no variations, it's a hanging problem
                # otherwise, any variation is either a blunder or a candidate
                # find the first candidate if it exists, and work recursively
                candidates = [node for node in node.variations if 2 not in node.nags]
                if candidates:                    
                    search_node(candidates[0], solution_perspective)
                # work recursively on blunders with reversed perspective
                blunders = [node for node in node.variations if 2 in node.nags]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective)
                    

        # call it on all children of the root node
        solution_perspective = self._data.perspective                        
        search_node(self._game, solution_perspective)

        return solutions


class ZugSolutionData():

    def __init__(
            self,
            status: str = ZugSolutionStatus.UNLEARNED,
            last_study_date: datetime.date = ZugDates.yesterday(),
            due_date: datetime.date = ZugDates.yesterday(),
            successes: int = 0,
            failures: int = 0,
    ):
        self.status = status
        self.last_study_date = last_study_date
        self.due_date = due_date
        self.successes = successes
        self.failures = failures

    def __eq__(self, other) -> bool:
        return all(
            (
                self.status == other.status,
                self.last_study_date == other.last_study_date,
                self.due_date == other.due_date,
                self.successes == other.successes,
                self.failures == other.failures,
            )
        )

    @classmethod
    def from_comment(cls, comment: str):
        data = comment.split(';')
        status = data[0].split('=')[1]
        last_study_date = data[1].split('=')[1]
        last_study_date = datetime.datetime.strptime(last_study_date, '%d-%m-%Y').date()
        due_date = data[2].split('=')[1]
        due_date = datetime.datetime.strptime(due_date, '%d-%m-%Y').date()
        successes = int(data[3].split('=')[1])
        failures = int(data[4].split('=')[1])
        return ZugSolutionData(status, last_study_date, due_date, successes, failures)

    def make_comment(self) -> str:
        return ';'.join(
            (
                f'status={self.status}',
                f'last_study_date={self.last_study_date.strftime("%d-%m-%Y")}',
                f'due_date={self.due_date.strftime("%d-%m-%Y")}',
                f'successes={self.successes}',
                f'failures={self.failures}'
            )
        )

    def update(self, changes):
        for key, val in changes.items():
            setattr(self, key, val)


class ZugSolution():

    def __init__(self, node: chess.pgn.ChildNode, root: ZugRoot):
        self._data = ZugSolutionData.from_comment(node.comment)
        self._node = node
        self._root = root

    @property
    def node():
        return self._node
        
    def update_node_comment(self):
        self._node.comment = self.data.make_comment()

    def learned(self):
        self._root.decrement_learning_remaining()
        self._data.update(
            {
                'status': ZugSolutionStatus.LEARNED,
                'last_study_date': ZugDates.today(),
                'due_date': ZugDates.tomorrow(),
                'successes': self.data.successes + 1,
            }
        )
        
    def recalled(self):
        next_due_date = ZugDates.due_date(
            self._data.last_study_date,
            self._data.due_date,
            self._root.recall_radius,
            self._root.recall_factor
        )
        self._data.update(
            {
                'successes': self.data.successes + 1,
                'last_study_date': ZugDates.today(),
                'due_date': next_due_date,
            }
        )
        
    def forgotten(self):
        self._data.update(
            {
                'status': ZugSolutionStatuses.UNLEARNED,                
                'failures': self._data.failures + 1,
            }
        )
