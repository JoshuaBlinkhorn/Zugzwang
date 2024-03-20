from typing import List
import chess
import chess.pgn
import json
import datetime


class ZugJsonError(Exception):
    pass


class ZugJsonDecodeError(ZugJsonError):
    pass


class ZugJsonEncodeError(ZugJsonError):
    pass


class ZugJsonTools:
    @staticmethod
    def _json_conversion(value):
        # convert datetime.date to ISO date string
        # leave all other values unchanged
        if isinstance(value, datetime.date):
            return value.isoformat()
        raise TypeError("Cannot serialise python object in JSON.")

    @classmethod
    def encode(cls, data_dict):
        """Encode a dictionary of data as a json string"""
        if not isinstance(data_dict, dict):
            raise ZugJsonEncodeError("Non-dictionary is not decodable")

        return json.dumps(data_dict, default=cls._json_conversion)

    @staticmethod
    def decode(json_string):
        """Decode a json string into a dictionary"""
        try:
            data_dict = json.loads(json_string)
        except json.JSONDecodeError:
            raise ZugJsonDecodeError("String is not decodeable")

        if not isinstance(data_dict, dict):
            raise ZugJsonDecodeError("Decoded object is not a dictionary")

        for key, val in data_dict.items():
            # Convert ISO format data strings into datetime.date
            try:
                data_dict[key] = datetime.date.fromisoformat(val)
            except (TypeError, ValueError):
                pass

        return data_dict


class ZugStringError(Exception):
    pass


class ZugStringDelimiterError(ZugStringError):
    pass


class ZugStringTools:
    @staticmethod
    def to_square_braces(string: str) -> str:
        if not isinstance(string, str):
            raise TypeError(f"{string} is not a string.")

        if not (string.startswith("{") and string.endswith("}")):
            raise ZugStringDelimiterError(
                f"String not delimited by curly braces: {string}"
            )

        return string.replace("{", "[").replace("}", "]")

    @staticmethod
    def to_curly_braces(string: str) -> str:
        if not isinstance(string, str):
            raise TypeError(f"{string} is not a string.")

        if not (string.startswith("[") and string.endswith("]")):
            raise ZugStringDelimiterError(
                f"String not delimited by square braces: {string}"
            )

        return string.replace("[", "{").replace("]", "}")


class ZugChessToolsError(Exception):
    pass


class ZugChessToolsParseError(ZugChessToolsError):
    pass


class ZugChessTools:
    @classmethod
    def get_solution_nodes(
        cls, game: chess.pgn.Game, perspective: bool
    ) -> List[chess.pgn.ChildNode]:
        # define a list to store solutions and a recursive search function
        solutions = []

        def search_node(node: chess.pgn.GameNode, solution_perspective: bool):
            nonlocal solutions
            player_to_move = node.board().turn
            if player_to_move != solution_perspective:
                # the node is a solution or an alternative
                # if it's solution, add it to the solution set
                if node != game and node.nags == set():
                    solutions.append(node)
                # work recursively on all children
                for problem in node.variations:
                    search_node(problem, solution_perspective)
            else:
                # the node is a problem
                # if it has no variations, it's a hanging problem
                # otherwise, any variation is either a blunder or a candidate
                # find the first candidate if it exists, and work recursively
                replies = node.variations
                candidates = [node for node in replies if node.nags == set()]
                if candidates:
                    solution = candidates[0]
                    search_node(solution, solution_perspective)
                alternatives = [node for node in replies if node.nags == {5}]
                for alternative in alternatives:
                    search_node(alternative, solution_perspective)
                # work recursively on blunders with reversed perspective
                blunders = [node for node in replies if node.nags == {2}]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective)

        # call it on the root node
        search_node(game, perspective)

        return solutions

    @classmethod
    def get_lines(
        cls, game: chess.pgn.Game, perspective: bool
    ) -> List[chess.pgn.GameNode]:

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
            prefix: List[chess.pgn.GameNode],
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
                replies = node.variations
                candidates = [node for node in replies if node.nags == set()]
                if candidates:
                    solution = candidates[0]
                    search_node(solution, solution_perspective, prefix)
                alternatives = [node for node in replies if node.nags == {5}]
                for alternative in alternatives:
                    for node in alternative.variations:
                        search_node(node, solution_perspective, [])
                # work recursively on blunders with reversed perspective
                # and a new prefix starting at the blunder
                blunders = [node for node in node.variations if node.nags == {2}]
                for blunder in blunders:
                    search_node(blunder, not solution_perspective, [])

        # call it on the root node
        search_node(game, perspective, [])

        return lines
