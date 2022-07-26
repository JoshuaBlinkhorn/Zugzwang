# ad hoc script to prepare a naked .pgn as a .chp with default comments
# run it from within a dir containing your naked pgns
# it will output a default chapter with the same filename, modulo the extension

import sys
import os
import chess

from zugzwang.constants import ZugColours
from zugzwang.chapter import ZugChapter
from zugzwang.game import ZugRoot, ZugRootData, ZugSolutionData

# range over the filenames in the current directory
pgn_files = os.listdir()
for filename in pgn_files:
    
    if not filename.endswith('pgn'):
        print(f"Skipping '{filename}'")
        continue
    
    colour = None
    while colour != 'w' and colour != 'b':
        colour = input(f"Select perspective for '{filename}' [w/b]:'")
    if colour == 'w':
        perspective = ZugColours.WHITE
    else:
        perspective = ZugColours.BLACK
        
    with open(filename) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
    root_data = ZugRootData(perspective)
    game.comment = root_data.make_json()
    root = ZugRoot(game)
    game.comment = ZugChapter._to_square_braces(game.comment)
    for sol_node in root.solution_nodes():
        sol_node.comment = ZugChapter._to_square_braces(ZugSolutionData().make_json())

    output_filename = filename.replace('.pgn','.chp')
    print(game, file=open(output_filename, 'w'))        
    
