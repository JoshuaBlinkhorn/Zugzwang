# usage:
# enforce-stub.py <stub> <source-dir> <target-dir>
#
# Find all leaf nodes of the stub with perspective not to move
# Search for those positions amonst the PGNs in source and create
# PGNs starting from those leaves, placing them in target

import sys
import chess
import chess.pgn
import pathlib
import random

from typing import List, Dict

stub = pathlib.Path(sys.argv[1])
source_dir = pathlib.Path(sys.argv[2])
target_dir = pathlib.Path(sys.argv[3])


def get_words() -> List[str]:
    with open("/Users/joshuablinkhorn/Training/Zugzwang/words.txt") as f:
        words = f.readlines()
    return [word[:-1] for word in words if len(word) > 3]


def three_random_words(words: List[str]) -> str:
    random.shuffle(words)
    three = words[:3]
    return "".join([word[0].upper() + word[1:] for word in three])


def find_fens(
    node: chess.pgn.GameNode,
    perspective: bool,
    fens: List[str],
):
    if node.is_end():
        board = node.board()
        if board.turn != perspective:
            fens.append(board.fen())
    else:
        for child in node.variations:
            find_fens(child, perspective, fens)


def find_source_node(fen: str, node: chess.pgn.GameNode):
    if node.board().fen() == fen:
        return node
    for child in node.variations:
        if (node := find_source_node(fen, child)) is not None:
            return node


def game_from_fen(
    fen: str,
    source_node: chess.pgn.Game,
    perspective: bool,
) -> chess.pgn.Game:
    key = "White" if perspective else "Black"
    headers = {key: "p"}
    board = chess.Board(fen=fen)

    game = chess.pgn.Game(headers=headers)
    game.setup(board)
    game.variations = source_node.variations

    return game


def write_game(game: chess.pgn.Game, target: pathlib.Path):
    print(game, file=open(target, "w"))


if __name__ == "__main__":
    words = get_words()
    with open(stub) as pgn:
        stub_game = chess.pgn.read_game(pgn)
    perspective = stub_game.headers["White"] == "p"
    fens = []
    find_fens(stub_game, perspective, fens)

    sources = []
    for source in source_dir.iterdir():
        if source == stub:
            continue
        with open(source) as pgn:
            sources.append(chess.pgn.read_game(pgn))

    fens_map = {}
    for fen in fens:
        for source in sources:
            if (node := find_source_node(fen, source)) is not None:
                fens_map[fen] = node
                break

    for fen, source_node in fens_map.items():
        game = game_from_fen(fen, source_node, perspective)
        game_filename = pathlib.Path(f"{three_random_words(words)}.pgn")
        target = target_dir / game_filename
        print(game, file=open(target, "w"))
