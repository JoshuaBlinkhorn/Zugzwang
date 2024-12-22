from typing import List, Optional
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


def _is_solution(node: chess.pgn.GameNode, perspective: bool) -> bool:
    return node.board().turn != perspective and node.move is not None


def _is_problem(node: chess.pgn.GameNode, perspective: bool) -> bool:
    return node.board().turn == perspective


def _is_blunder(node: chess.pgn.GameNode) -> bool:
    return 2 in node.nags or 4 in node.nags


def _is_alternative(node: chess.pgn.GameNode) -> bool:
    return 5 in node.nags


def _has_solution(problem: chess.pgn.GameNode) -> bool:
    return any(not _is_blunder(child) for child in problem.variations)


def _get_solution(problem: chess.pgn.GameNode) -> Optional[chess.pgn.GameNode]:
    candidates = [
        child
        for child in problem.variations
        if not _is_blunder(child) and not _is_alternative(child)
    ]

    if len(candidates) == 0:
        return None

    if len(candidates) > 1:
        import pdb

        pdb.set_trace()
        raise ZugChessToolsParseError("Problem has ambiguous solution.")

    return candidates.pop()


def _get_alternatives(problem: chess.pgn.GameNode) -> List[chess.pgn.GameNode]:
    return [child for child in problem.variations if _is_alternative(child)]


def _get_blunders(problem: chess.pgn.GameNode) -> List[chess.pgn.GameNode]:
    return [child for child in problem.variations if _is_blunder(child)]


def _is_line_end(solution: chess.pgn.GameNode):
    return not any(_has_solution(problem) for problem in solution.variations)


def get_lines(
    game: chess.pgn.Game, perspective: bool
) -> List[List[chess.pgn.GameNode]]:
    lines = []

    def search_node(
        node: chess.pgn.GameNode,
        perspective: bool,
        prefix: List[chess.pgn.GameNode],
    ) -> None:
        nonlocal lines
        prefix = prefix.copy()

        if _is_problem(node, perspective):
            problem = node
            prefix.append(problem)
            if solution := _get_solution(problem):
                search_node(solution, perspective, prefix)
            for alternative in _get_alternatives(problem):
                for sub_problem in alternative.variations:
                    search_node(sub_problem, perspective, list())
            for blunder in _get_blunders(problem):
                search_node(blunder, not perspective, list())

        else:
            if _is_solution(node, perspective):
                prefix.append(node)
            if _is_line_end(node):
                lines.append(prefix)
            for problem in node.variations:
                search_node(problem, perspective, prefix)

    search_node(game, perspective, [])
    return [line for line in lines if line]


def get_solutions(
    game: chess.pgn.Game,
    perspective: bool,
) -> List[chess.pgn.ChildNode]:
    solutions = []

    def search_node(
        node: chess.pgn.GameNode,
        perspective: bool,
    ) -> None:
        nonlocal solutions

        if _is_problem(node, perspective):
            problem = node
            if solution := _get_solution(problem):
                search_node(solution, perspective)
            for alternative in _get_alternatives(problem):
                search_node(alternative, perspective)
            for blunder in _get_blunders(problem):
                search_node(blunder, not perspective)

        else:
            if _is_solution(node, perspective):
                solutions.append(node)
            for problem in node.variations:
                search_node(problem, perspective)

    search_node(game, perspective)
    return solutions
