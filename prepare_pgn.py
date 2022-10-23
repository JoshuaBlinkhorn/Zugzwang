# ad hoc script to prepare a naked .pgn as a .chp with default comments
# run it from within a dir containing your naked pgns
# it will output a default chapter with the same filename, modulo the extension

import sys
import os
import chess

from zugzwang.constants import ZugColours
from zugzwang.chapter import ZugChapter
from zugzwang.game import ZugRoot, ZugRootData, ZugSolutionData
from zugzwang.tools import ZugChessTools

# range over the filenames in the current directory
pgn_files = sorted(os.listdir())
for filename in pgn_files:

    # Try to determine perspective based on filename
    if not filename.endswith('pgn'):
        print(f"Skipping '{filename}'")
        continue
    if filename[-5] in 'wW':
        perspective = ZugColours.WHITE
    elif filename[-5] in 'bB':
        perspective = ZugColours.BLACK

    # Otherwise, ask user for perspective
    else:
        colour = None
        while colour != 'w' and colour != 'b':
            colour = input(f"Select perspective for '{filename}' [w/b]:'")
        if colour == 'w':
            perspective = ZugColours.WHITE
        else:
            perspective = ZugColours.BLACK

    output_filename = filename.replace('.pgn','.chp')            
    with open(filename) as pgn_file, open(output_filename, 'w') as output_file:

        game = chess.pgn.read_game(pgn_file)
        while game is not None:            
            # look to set the perspective from the game header
            # override perspective if found
            if game.headers['White'] == 'p':
                perspective = ZugColours.WHITE
                print('Set perspective = WHITE based on game header')
            if game.headers['Black'] == 'p':
                perspective = ZugColours.BLACK
                print('Set perspective = BLACK based on game header')

            # set the root data on the root comment
            root_data = ZugRootData(perspective=perspective)
            game.comment = root_data.as_string()
            
            print(game, '\n', file=output_file)
            game = chess.pgn.read_game(pgn_file)
    
