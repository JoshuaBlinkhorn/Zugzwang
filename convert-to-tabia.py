import os
from typing import List
import random

import chess.pgn


def get_words() -> List[str]:
    with open("/Users/joshuablinkhorn/Training/Zugzwang/words.txt") as f:
        words = f.readlines()
    return [word[:-1] for word in words if len(word) > 3]


def three_random_words(words: List[str]) -> str:
    random.shuffle(words)
    three = words[:3]
    return "".join([word[0].upper() + word[1:] for word in three])


def clean_node(node: chess.pgn.GameNode) -> None:
    node.comment = ""
    for child in node.variations:
        clean_node(child)


mapper = {
    "1-the-dangerous-corner.pgn": "DangerousCorner",
    "2-the-safe-corner.pgn": "SafeCorner",
    "3-a-bishop-pawn.pgn": "BishopsPawn",
}

filenames = os.listdir()
words = get_words()

for filename in mapper:
    dir_name = mapper[filename]
    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)
    pgn = open(filename)
    game = chess.pgn.read_game(pgn)
    while game:
        clean_node(game)
        game_filename = f"{three_random_words(words)}.pgn"
        print(game, file=open(f"{dir_name}/{game_filename}", "w"))
        game = chess.pgn.read_game(pgn)
