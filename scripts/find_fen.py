# Ad hoc script to list the tabias containing a fen position
import sys
import pathlib

import chess
from zugzwang.config import config
from zugzwang.group import Group, Tabia, Item, DefaultIOManager
from zugzwang.zugzwang import initialise_group


def search_node(node: chess.pgn.GameNode, fen: str) -> bool:
    node_fen = node.board().board_fen()
    if node_fen == fen:
        return True
    return any([search_node(child, fen) for child in node.variations])


if __name__ == "__main__":
    io_manager = DefaultIOManager()
    data_path = pathlib.Path(config["user_data"])
    user_data = initialise_group("UserData", data_path, io_manager)
    fen = sys.argv[1]

    print(f"Searching for fen {fen}..")

    names = [
        tabia.name
        for tabia in user_data.tabias()
        if search_node(tabia.game, fen) is True
    ]
    print(names)
