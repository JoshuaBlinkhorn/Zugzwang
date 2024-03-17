import os
from typing import List
import random

import chess.pgn

def get_words() -> List[str]:
    with open("/Users/joshuablinkhorn/Training/Zugzwang/words.txt") as f:
        words = f.readlines()
    return [word[:-1] for word in words if len(word) > 2]

def three_random_words(words: List[str]) -> str:
    random.shuffle(words)
    three = words[:3]
    return "".join([word[0].upper() + word[1:] for word in three])

def clean_node(node: chess.pgn.GameNode) -> None:
    node.comment = ""
    for child in node.variations:
        clean_node(child)

mapper = {
    "idea-of-reti.pgn": "Reti",
    "key-squares.pgn": "KeySquares",
    "mined-squares.pgn": "MinedSquares",
    "opposition.pgn": "Opposition",
    "other-correspondance.pgn": "Correspondance",
    "rule-of-the-square.pgn": "TheSquare",
    "triangulation.pgn": "Triangulation",
}
filenames = os.listdir()
words = get_words()

for filename in mapper:
    dir_name = mapper[filename]
    os.mkdir(dir_name)
    pgn = open(filename)
    game = chess.pgn.read_game(pgn)
    while game:
        clean_node(game)
        game_filename = f"{three_random_words(words)}.pgn"
        print(game, file=open(f"{dir_name}/{game_filename}", "w"))
        game = chess.pgn.read_game(pgn)
