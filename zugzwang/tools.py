from typing import List
import chess

class ZugChessTools:

    @classmethod
    def get_solution_nodes(
            cls,
            game: chess.pgn.Game,
            perspective: bool
    ) -> List[chess.pgn.ChildNode]:
        # define a list to store solutions and a recursive search function
        solutions = []
        def search_node(
                node: chess.pgn.GameNode,
                solution_perspective: bool
        ):
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution
                # add it to the set and work recursively on all children
                if node != game:
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

        # call it on the root node
        search_node(game, perspective)

        return solutions

    @classmethod
    def get_lines(
            cls,
            game: chess.pgn.Game,
            perspective: bool
    ) -> List[chess.Board]:

        # define an empty list to store the lines and a recursive search function        
        lines = []

        def is_blunder(node: chess.pgn.GameNode):
            return 2 in node.nags
                       
        def has_solution(problem: chess.pgn.GameNode):
            return any(not is_blunder(child) for child in problem.variations)
        
        def is_line_end(solution: chess.pgn.GameNode):
            # determining whether a given node is the end of a line is quite complex
            # to illustrate: a solution S may have a child problem P, such that P
            # has no child solution T, but it has a child blunder B
            # if P is the only child of S, then S is the end of the line
            #
            # the simplest characterisation is: the line ends at a solution unless
            # there exists a child problem with a child solution
            return not any(has_solution(problem) for problem in solution.variations)
        
        def search_node(
                node: chess.pgn.GameNode,
                solution_perspective: bool,
                prefix: List[chess.pgn.GameNode]
        ):
            # copy the prefix; necessary because otherwise all branches would modify
            # the same prefix 
            # it's easist to do this once, here at the top of the function
            prefix = prefix.copy()
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution
                # append it to the prefix if and only if it is not the root
                if node != game:
                    prefix.append(node)                
                # if the line ends here, add it to the set of lines
                # otherwise, work recursively on all children
                if is_line_end(node):
                    lines.append(prefix)
                for problem in node.variations:
                    search_node(problem, solution_perspective, prefix)
            else:
                # the node is a problem; append it to the prefix
                prefix.append(node)
                # if it has no variations, it's a hanging problem, ignore it
                # otherwise, any variation is either a candidate or a blunder
                # find the first candidate if it exists, and work recursively
                candidates = [node for node in node.variations if 2 not in node.nags]
                if candidates:
                    candidate = candidates[0]
                    search_node(candidate, solution_perspective, prefix)
                # work recursively on blunders with reversed perspective
                # and a new prefix starting at the blunder
                blunders = [node for node in node.variations if 2 in node.nags]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective, [])
        
        # call it on the root node
        search_node(game, perspective, [])

        return lines


