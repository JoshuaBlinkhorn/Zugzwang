# ad hoc script to prepare a stub .pgn as a zugzwang pgn
# this means adding the default comment to the root node
# run it from Zugzwang root dir, passing the target dir absolute path as a parameter.
# the script will find any PGN with -STUB in its name
# and generate and save a zugzwang PGN with -STUB removed from the name

# a stub PGN should indicate the perspective with a 'p' as one of the player names
# if no perspective is indicate, I believe it defaults to white

import sys
import os
import chess

from zugzwang.constants import ZugColours
from zugzwang.chapter import ZugChapter
from zugzwang.game import ZugRoot, ZugRootData, ZugSolutionData
from zugzwang.tools import ZugChessTools

target_dir = sys.argv[1]

# range over the filenames in the current directory
pgn_files = sorted(os.listdir(target_dir))
for filename in pgn_files:

    if "-STUB" not in filename:
        continue

    input_filename = os.path.join(target_dir, filename)
    output_filename = os.path.join(target_dir, filename.replace("-STUB", ""))
    with open(input_filename) as pgn_file, open(output_filename, "w") as output_file:

        game = chess.pgn.read_game(pgn_file)
        while game is not None:
            # look to set the perspective from the game header
            # override perspective if found
            if game.headers["White"] == "p":
                perspective = ZugColours.WHITE
                print("Set perspective = WHITE based on game header")
            if game.headers["Black"] == "p":
                perspective = ZugColours.BLACK
                print("Set perspective = BLACK based on game header")

            # set the root data on the root comment
            root_data = ZugRootData(perspective=perspective)
            game.comment = root_data.as_string()

            print(game, "\n", file=output_file)
            game = chess.pgn.read_game(pgn_file)
