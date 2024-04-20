import os
from typing import List
import random

import chess.pgn


grunfeld_path = "/Users/joshuablinkhorn/Training/Collections/Grunfeld"


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


dirs = os.listdir(grunfeld_path)
for dir_ in dirs:
    if not os.path.isdir(dir_):
        os.mkdir(dir_)
    dir_path = "/".join([grunfeld_path, dir_])
    filenames = os.listdir(dir_path)

    for filename in filenames:
        file_path = "/".join([dir_path, filename])
        words = get_words()
        pgn = open(file_path)
        game = chess.pgn.read_game(pgn)
        while game:
            clean_node(game)
            game_filename = f"{three_random_words(words)}.pgn"
            print(game, file=open(f"{dir_}/{game_filename}", "w"))
            game = chess.pgn.read_game(pgn)
