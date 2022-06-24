##########################
# chessic -- version 2.0 #
# chess position trainer #
# joshua blinkhorn       #
##########################

# TODO - implement collection backup on startup

# Hierarchy of user data

# Collection (eg White Repertoire, Endgames)
# - Category (eg Sicilian Defence, Rook + Pawn vs Rook)
#   - Item   (eg Najdorf Variation, Lucena Position)

# terminology:

# the `root node' is the first node in a parsed pgn. It is identified with
# the starting position given in the FEN field of the PGN header
# The training player's opponent must have the move in the position
# represented by the root node.

# a 'problem' is a node representing a position in which the training player
# ('player') is to move. This can be identified with the move played
# by the training player's opponent ('opponent') leading to this position.

# a 'solution' is a node representing a position in which the opponent
# is to move, following a move by the player played. This can be
# identified with player's move leading to this position
# The root node is not a solution. Solutions are also referred to as
# `training nodes', since they hold training data.

#############
# libraries #
#############

import os
import chess
import chess.pgn
import random
import time
import datetime
import shutil
from colorama import Fore, Back, Style

#############
# constants #
#############

# training node statuses
NEW = 0
FIRST_STEP = 1
SECOND_STEP = 2
REVIEW = 3
INACTIVE = 4

# statistics indexes
STATS_NEW = 0
STATS_FIRST_STEP = 1
STATS_SECOND_STEP = 2
STATS_REVIEW = 3
STATS_INACTIVE = 4
STATS_DUE = 5
STATS_TOTAL = 6

# meta data indexes for string parsing
LAST_ACCESS = 0 
NEW_REMAINING = 1
NEW_LIMIT = 2

# training data indexes for string parsing
STATUS = 0
LAST_DATE = 1
DUE_DATE = 2
SUCCESSES = 3
FAILURES = 4

# key-value pair indexes for string parsing
KEY = 0
VALUE = 1

# permutation for flipping the board
board_flip = [63,62,61,60,59,58,57,56,55,54,53,52,51,50,49,48,47,46,45,44,43,42,41,40,39,38,37,36,35,34,33,32,31,30,29,28,27,26,25,24,23,22,21,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,0]

# unicode values of pieces
white_pieces = ['\u2654','\u2655','\u2656','\u2657','\u2658','\u2659']
black_pieces = ['\u265a','\u265b','\u265c','\u265d','\u265e','\u265f']

# path to data directory
data_path = "Collections"

##########################
# date-string conversion #
##########################

def string_from_date(date) :
    return date.strftime("%d-%m-%Y")

def date_from_string(string) :
    return datetime.datetime.strptime(string,"%d-%m-%Y").date()

#########################
# training data classes #
#########################

class TrainingData :
    def __init__(self) :
        self.status = INACTIVE
        self.last_date = datetime.date.today()
        self.due_date = datetime.date.today()
        
class MetaData:
    def __init__(self, name, player) :
        self.name = name
        self.player = player
        self.learning_data = [datetime.date.today(),0]
        self.learn_max = 10

########################
# uci notation / input #
########################

# checks whether a string represents an integer
def represents_int(string):
    try: 
        int(string)
        return True
    except ValueError:
        return False

# checks whether a string is a legal move in uci notation
def is_valid_uci(string,board) :
    for move in board.legal_moves :
        if (string == move.uci()) :
            return True
    return False

############
# printing #
############

# `clears' the screen
def clear() :
    for _ in range(40) :
        print("")

# prints the side to move
# TODO - put this as an icon on the board itself
def print_turn(board) :
    print("")
    if (board.turn) :
        print("WHITE to play.")
    else :
        print("BLACK to play.")

# places the python chess unicode string into 64-char array
def pack_string(string) :
    array = []
    for index in range(64) :
        array += string[index * 2]
    return array
        
# pretty prints the board
def print_board(board,player) :
    
    # convert python chess unicode board into array of 64 characters
    array = pack_string(board.unicode(invert_color = False, empty_square = " "))
    if (not player) :
        new_array = array.copy()
        for index in range(64) :
            new_array[index] = array[board_flip[index]]
        array = new_array

    board_string = ""
    for row in range(8) :
        for column in range(8) :
            index = (row * 8) + column
            # set piece colour
            if (array[index] in white_pieces) :
                piece_colour = Fore.WHITE
            else :
                piece_colour = Fore.BLACK

            # for uniform treatment of chess characters
            if (array[index] in black_pieces) :
                array[index] = white_pieces[black_pieces.index(array[index])]

            # set background colour
            case_1 = column % 2 == 1 and row % 2 == 1
            case_2 = column % 2 == 0 and row % 2 == 0
            if (case_1 or case_2) :
                square_colour = Back.CYAN
            else :
                square_colour = Back.GREEN

            # write square
            board_string += (square_colour + piece_colour + array[index] + ' ')
            
        board_string += (Style.RESET_ALL)
        if (row < 7) :
            board_string += '\n'

    print(board_string)

# prints repertoire moves for the given node
def print_moves(node) :
    if (node.player_to_move) :
        if (node.is_end()) :
            print("\nNo solutions.")
        else :
            print("\nSolutions:")
            for solution in node.variations :
                print(solution.move.uci())
    else :
        if (node.is_end()) :
            print("\nNo problems.")
        else :
            print("\nProblems:")
            for problem in node.variations :
                print(problem.move.uci())

##################
# pgn management #
##################

# removes the file extension from a pgn filename
def pgn_name(filename) :
    return filename[:-4]

# default meta/training data strings
# these strings are added as default comments to the root node and
# and training nodes the first time they are encountered
# yesterday is used as a default past date
def default_meta_data_string() :
    today = datetime.date.today()
    yesterday = string_from_date(today - datetime.timedelta(days = 1))
    return "last_access=" + yesterday + ";new_remaining=10;new_limit=10;"

def default_training_data_string() :
    today = datetime.date.today()
    yesterday = string_from_date(today - datetime.timedelta(days = 1))
    string = "status=INACTIVE;last_date=" + yesterday + ";due_date=" 
    string += yesterday + ";successes=0;failures=0;"
    return string

# adds default training data to pgn comments, where it is lacking
# this can happen if the pgn is newly encountered, in which case
# default meta data is added to the root node and default training
# data to all training nodes, or if new moves have been
# added externally, in which case default training data is added
# to the appropriate training nodes
def add_default_data(node) :
    # determine whether this is the root node
    # if so, add the default meta data string to root node if needed
    if (node == node.game()) :
        if (node.comment == "") :
            node.comment = default_meta_data_string()
    # if not, determine whether this node is a training node
    else :
        player = not node.game().board().turn
        if (node.board().turn != player and node.comment == "") :
            node.comment = default_training_data_string()
    # work recursively on all nodes
    for child in node.variations :
        add_default_data(child)

# Updates meta and training data, usually after a period of absense.
# This involves, for example, setting the status of training nodes
# and the meta data last_access and new_remaining.
# The parameter `space' describes how many more nodes may take the
# status "NEW". When first called on the root node, this parameter
# should equal root.new_remaining. In the recursive process, applicable
# training nodes (i.e. those whose status is not "REVIEW")
# are set to "NEW" on a first-come-first-served basis, and the space
# paramenter is decremented each time. All remaining non-review nodes are
# set "INACTIVE". This means that "FIRST_STEP" and "SECOND_STEP" training
# nodes are reset, i.e. incomplete learning is destroyed.
# The overall effect is that the first 'new_remaining'-many non-review nodes
# are set to "NEW", review nodes are unchanged, all other nodes are
# set to "INACTIVE"

# Recursion takes place only on the subtree defined by the chosen solution,
# i.e. the main varation at a problem node. Sub variations are not traversed,
# so the training data there is preserved.

# This function should be called immediately after any changes to the PGN
# or the meta data are made, and immediately before any training session
# begins. Hence the new_limit should probably not be reset while
# training is in progress.
def update_data(node, space) :
    today = datetime.date.today()
    player = not node.game().board().turn
    # determine whether this is the root node
    # if so, update the meta data if the last access was before today
    if (node == node.game()) :
        if (node.last_access < today) :
            node.last_access = today
            node.new_remaining = node.new_limit
    # if not, determine whether this node is a training node
    else :
        if (node.board().turn != player) :
            if (space <= 0 and node.status != "REVIEW") :
                node.status = "INACTIVE"
            if (space > 0 and node.status != "REVIEW") :
                node.status = "NEW"
                space = space - 1
            node.comment = default_training_data_string()
    # work recursively, but only on main variations for problems
    if (node.board().turn == player and not node.is_end()) :
        space = update_data(node.variations[0],space)
    if (node.board().turn != player) :
        for child in node.variations :
            space = update_data(child,space)
    # return the available space to the calling function
    return space

# writes the current parsed PGN data structure back over the PGN file
def save_pgn(pgn, item_path) :
    print(pgn, file=open(item_path, "w"))

# appends meta and training data from the comments of the pgn as
# attributes to the appropriate nodes. since there is a relatively
# small set of data, it is appended directly to the nodes, one attribute
# per datum. While this is probably unpythonic, it is simple, and it works.
# A significant future increase in the size of this dataset seems unlikely
# This function should only be called on a newly opened pgn after update(),
# otherwise it may try to parse comments that are not there
def append_data(node) :    
    # determine whether this is the root node
    # if so, parse the comment and append the meta data
    if (node == node.game()) :
        meta_data = node.comment.split(';')
        date_string = meta_data[LAST_ACCESS].split('=')[VALUE]
        node.last_access = date_from_string(date_string)
        node.new_remaining = int(meta_data[NEW_REMAINING].split('=')[VALUE])
        node.new_limit = int(meta_data[NEW_LIMIT].split('=')[VALUE])
    # if not, determine whether this node is a training node
    # if so, parse the comment and append the training data
    else :
        player = not node.game().board().turn
        if (node.board().turn != player) :
            training_data = node.comment.split(';')
            node.status = training_data[STATUS].split('=')[VALUE]
            last_date_string = training_data[LAST_DATE].split('=')[VALUE]
            due_date_string = training_data[DUE_DATE].split('=')[VALUE]
            node.last_date = date_from_string(last_date_string)
            node.due_date = date_from_string(due_date_string)
            node.successes = int(training_data[SUCCESSES].split('=')[VALUE])
            node.failures = int(training_data[FAILURES].split('=')[VALUE])
    # work recursively on all nodes
    for child in node.variations :
        append_data(child)

# Updates the PGN comments (in the parsed data structure) with the
# current meta and training data. That data, which is appended as
# node attributes, is packed back into a string. This string is stored
# as the node attribute `comment', overwriting the existing comment.
def rewrite_pgn_comments(node) :
    # determine whether this is the root node
    # if so, build the comment and append it
    if (node == node.game()) :
        comment = "last_access=" + string_from_date(node.last_access) + ";" \
            + "new_remaining=" + str(node.new_remaining) + ";" \
            + "new_limit=" + str(node.new_limit) + ";"
        node.comment = comment
    # if not, determine whether this node is a training node
    # if so, parse the comment and append the training data
    else :
        player = not node.game().board().turn
        if (node.board().turn != player) :
            comment = "status=" + node.status + ";" \
                + "last_date=" + string_from_date(node.last_date) + ";" \
                + "due_date=" + string_from_date(node.due_date)+ ";" \
                + "successes=" + str(node.successes) + ";" \
                + "failures=" + str(node.failures) + ";"
            node.comment = comment
    # work recursively on all nodes
    for child in node.variations :
        rewrite_pgn_comments(child)

# Opens a pgn, ready for obtaining statistics or training.
# Since the pgn may have been edited elsewhere since it was last
# opened, open_pgn() goes through the worst-case routine every time.
# First default data is added to nodes, then data is updated due,
# then the pgn file is overwritten and the parsed pgn returned
# This may be over cautious, but performance is not crucial here
def open_pgn_on_startup(item_path) :
    pgn = chess.pgn.read_game(open(item_path))
    add_default_data(pgn)
    append_data(pgn)
    update_data(pgn,pgn.new_remaining)
    rewrite_pgn_comments(pgn)
    print(pgn, file = open(item_path, "w"))
    return pgn

def open_pgn(item_path) :
    pgn = chess.pgn.read_game(open(item_path))
    append_data(pgn)    
    return pgn

def close_pgn(pgn, item_path) :
    rewrite_pgn_comments(pgn)
    print(pgn, file = open(item_path, "w"))

##############
# statistics #
##############

# Searches the pgn tree recursively and gathers statistics, namely
# the number of occurrences of each status and the total
# number of positions (i.e. including non-mainline solutions).
# The occurrences of statuses are only counted in mainline solutions,
# which specify the user's current repertoire. Hence the number of reachable
# training nodes is the sum of the status occurrences.
# when called initially, stats_list should be a list of six zeros
def get_stats(pgn,stats_list) :
    total = 0
    today = datetime.date.today()
    status_stats(pgn,stats_list,today)
    total_stat(pgn,stats_list)

def status_stats(node, stats_list, today) :
    player = not node.game().board().turn
    # determine whether this node is a training node
    # if so, increment the status count
    if (node != node.game() and node.board().turn != player) :
        status = node.status
        if (status == "NEW") :
            stats_list[STATS_NEW] += 1
        if (status == "FIRST_STEP") :
            stats_list[STATS_FIRST_STEP] += 1
        if (status == "SECOND_STEP") :
            stats_list[STATS_SECOND_STEP] += 1
        if (status == "REVIEW") :
            stats_list[STATS_REVIEW] += 1
            if (node.due_date <= today) :
                stats_list[STATS_DUE] += 1
        if (status == "INACTIVE") :
            stats_list[STATS_INACTIVE] += 1
    # work recursively, visiting only mainline solutions
    if (node.board().turn == player) :
        if (not node.is_end()) :
            status_stats(node.variations[0], stats_list, today)
    else :
        for child in node.variations :
            status_stats(child, stats_list, today)

def total_stat(node,stats_list) :
    player = not node.game().board().turn
    # determine whether the current node is a training node
    # if so, increment total counter
    if (node != node.game() and node.board().turn != player) :
        stats_list[STATS_TOTAL] += 1
    # work recursively over the whole pgn    
    for child in node.variations :
        total_stat(child,stats_list)
        
#########
# menus #
#########

# Prints the Chessic main menu. This is a list of the available collections,
# their statistics, and a prompt
def main_menu():
    # obtain list of collections, and deal with an empty list
    collections = os.listdir(data_path)
    if (len(collections) == 0) :
        print("You have no collections.")
        print("You must first create a collection to train with chessic.")
        print("See the accompanying manual.")
        return None
    # print the collections menu, options and prompt
    # the whole printed script merely clears and reprints until
    # intelligible input is given
    # note that this repeatedly opens pgn, which performs various other
    # precautionary proceedures. This is clearly non-optimal, but given
    # a small amount of user collection data it should not be noticable.
    command = ""
    while(command != "c") :
        collections.sort()
        clear()
        # print header
        header = "ID".ljust(3) + "COV.".ljust(5) + "COLLECTION".ljust(20)
        header += "WAITING".ljust(9) + "LEARNED".ljust(9)
        header += "TOTAL".ljust(6)
        print(header)    
        # print the stats for each collection
        for index, collection in enumerate(collections) :
            waiting = learned = total = 0
            collection_path = data_path + "/" + collection
            for category in os.listdir(collection_path) :
                category_path = collection_path + "/" + category
                for item in os.listdir(category_path) :
                    item_path = category_path + "/" + item
                    pgn = open_pgn_on_startup(item_path)
                    stats = [0,0,0,0,0,0,0]
                    get_stats(pgn,stats)
                    learning = stats[STATS_NEW] + stats[STATS_FIRST_STEP] \
                        + stats[STATS_SECOND_STEP]
                    waiting += learning + stats[STATS_DUE]
                    learned += stats[STATS_REVIEW]
                    total += learning + learned + stats[STATS_INACTIVE]
            id = index + 1
            info = str(id).ljust(3)
            if (total != 0) :
                coverage = int(round(learned / total * 100))
                info += (str(coverage) + "% ").rjust(5)
            else :
                info += "".ljust(5)
            info += collection.ljust(20)
            info += str(waiting).ljust(9)
            info += str(learned).ljust(9)
            info += str(total).ljust(7)
            print(info)
        # print user prompt
        print ("")
        if (len(collections) != 0) :
            print("[ID] select")
        print("'c' close")
        command = (input("\n:"))
        # process user input
        max_id = len(collections)
        if (represents_int(command) and 1 <= int(command) <= max_id) :
            index = int(command) - 1
            collection_menu(collections[index])

def collection_menu(collection) :
    # obtain list of collections, and deal with an empty list
    collection_path = data_path + "/" + collection
    categories = os.listdir(collection_path) 
    command = ""
    while(command != "c") :
        clear()
        if (len(categories) == 0) :
            print("You currently have no categories in this collection.")
            print("You must add categories to a collection to train with chessic.")
            print("See the accompanying manual.")
            print("\n'c' close")
            command = (input("\n:"))
        else :
            # print the collection menu, options and prompt
            # flow is as in the main menu        
            categories.sort()
            # print header
            header = "ID".ljust(3) + "COV.".ljust(5) + "CATEGORY".ljust(20)
            header += "WAITING".ljust(9) + "LEARNED".ljust(9)
            header += "TOTAL".ljust(6)
            print(header)    
            # print the stats for each collection
            for index, category in enumerate(categories) :
                waiting = learned = total = 0
                category_path = collection_path + "/" + category
                for item in os.listdir(category_path) :
                    item_path = category_path + "/" + item
                    pgn = open_pgn(item_path)
                    stats = [0,0,0,0,0,0,0]
                    get_stats(pgn,stats)
                    learning = stats[STATS_NEW] + stats[STATS_FIRST_STEP] \
                        + stats[STATS_SECOND_STEP]
                    waiting += learning + stats[STATS_DUE]
                    learned += stats[STATS_REVIEW]
                    total += learning + learned + stats[STATS_INACTIVE]
                id = index + 1
                info = str(id).ljust(3)
                if (total != 0) :
                    coverage = int(round(learned / total * 100))
                    info += (str(coverage) + "% ").rjust(5)
                else :
                    info += "".ljust(5)
                info += category.ljust(20)
                info += str(waiting).ljust(9)
                info += str(learned).ljust(9)
                info += str(total).ljust(7)
                print(info)
            # print user prompt
            print ("")
            if (len(categories) != 0) :
                print("[ID] select")
            print("'c' close")
            command = (input("\n:"))
            # process user input
            max_id = len(categories)
            if (represents_int(command) and 1 <= int(command) <= max_id) :
                index = int(command) - 1
                category_menu(collection, categories[index])

def category_menu(collection, category) :
    # obtain list of categories, and deal with an empty list
    category_path = data_path + "/" + collection + "/" + category
    items = os.listdir(category_path) 
    command = ""
    while(command != "c") :
        clear()        
        if (len(items) == 0) :
            print("You currently have no items in this category.")
            print("You must add items to a category to train with chessic.")
            print("See the accompanying manual.\n")
            print("'c' close")
            command = (input("\n:"))            
        else :
            # print the category menu, options and prompt
            # flow is as in the main menu
            items.sort()
            # print header
            header = "ID".ljust(3) + "COV.".ljust(5) + "ITEM".ljust(20)
            header += "WAITING".ljust(9) + "LEARNED".ljust(9)
            header += "TOTAL".ljust(6)
            print(header)    
            # print the stats for each collection
            for index, item in enumerate(items) :
                item_path = category_path + "/" + item
                pgn = open_pgn(item_path)
                stats = [0,0,0,0,0,0,0]
                get_stats(pgn,stats)
                learning = stats[STATS_NEW] + stats[STATS_FIRST_STEP] \
                    + stats[STATS_SECOND_STEP]
                waiting = learning + stats[STATS_DUE]
                learned = stats[STATS_REVIEW]
                total = learning + learned + stats[STATS_INACTIVE]

                id = index + 1
                info = str(id).ljust(3)
                if (total != 0) :
                    coverage = int(round(learned / total * 100))
                    info += (str(coverage) + "% ").rjust(5)
                else :
                    info += "".ljust(5)
                info += item[:-4].ljust(20)
                info += str(waiting).ljust(9)
                info += str(learned).ljust(9)
                info += str(total).ljust(7)
                print(info)
                # print user prompt
            print ("")
            if (len(items) != 0) :
                print("[ID] select")
            print("'c' close")
            command = (input("\n:"))
            # process user input
            max_id = len(items)
            if (represents_int(command) and 1 <= int(command) <= max_id) :
                index = int(command) - 1
                item_menu(collection, category, items[index])

def item_menu(collection, category, item) :
    tag_width = 14
    item_path = data_path + "/" + collection + "/" + category + "/" + item
    command = ""
    while(command != "c") :
        clear()
        # print header
        print("Item: " + item)

        # print sceduled counts
        pgn = open_pgn(item_path)
        stats = [0,0,0,0,0,0,0]
        get_stats(pgn,stats)    
        print("")
        print("New".ljust(tag_width) + str(stats[STATS_NEW]))
        print("Learning".ljust(tag_width) + str(stats[STATS_FIRST_STEP] + stats[STATS_SECOND_STEP]))
        print("Due".ljust(tag_width) + str(stats[STATS_DUE]))
        
        # print remaining counts
        reachable = stats[STATS_NEW] + stats[STATS_FIRST_STEP] + stats[STATS_SECOND_STEP] + stats[STATS_REVIEW] + stats[INACTIVE]
        print("")
        print("Learned".ljust(tag_width) + str(stats[STATS_REVIEW]))
        print("Unseen".ljust(tag_width) + str(stats[STATS_INACTIVE]))
        print("Reachable".ljust(tag_width) + str(reachable))
        print("Unreachable".ljust(tag_width) + str(stats[STATS_TOTAL] - reachable))

        # print user prompt
        print ("")
        print("'t' train")
        print("'c' close")
        command = (input("\n:"))
        # process user input
        if (command == 't') :
            train(item_path)

############
# training #
############

def train(item_path):
    pgn = open_pgn(item_path)
    player = not pgn.board().turn
    board = pgn.board()
    node = pgn        

    # generate queue
    queue = generate_training_queue(pgn,board,player)
    print(queue)

    # play queue
    command = ""
    while(len(queue) != 0) :
        card = queue.pop(0)
        stats = [0,0,0,0,0,0,0]
        get_stats(pgn,stats)        
        clear()
        print(f"{stats[0]} {stats[1]} {stats[2]} {stats[5]}")
        result = play_card(card,pgn)
        if (result == "CLOSE") :
            break
        handle_card_result(result,card,queue,pgn)

    # save and quit trainer
    close_pgn(pgn,item_path)

def generate_training_queue(node,board,player) :
    # the board must be returned as it was given
    queue = []

    if (hasattr(node,"status")) :
        print(str(node.status))
        status = node.status
        due_date = node.due_date
        today = datetime.date.today()
        if (status == "NEW" or status == "FIRST_STEP" or status == "SECOND_STEP" or (status == "REVIEW" and due_date <= today)) :
            print("here")

            # create card and add to the queue
            solution = board.pop()
            problem = board.pop()
            game = chess.pgn.Game()
            game.setup(board)
            new_node = game.add_variation(problem)
            new_node = new_node.add_variation(solution)
            board.push(problem)
            board.push(solution)
            queue.append([game,node])

    # recursive part
    if (not node.is_end()) :
        if (node.board().turn == player) :
            # search only the main variation
            child = node.variations[0]
            board.push(child.move)
            queue += generate_training_queue(child,board,player)
            board.pop()

        else :
            # search all variations
            for child in node.variations :
                board.push(child.move)
                queue += generate_training_queue(child,board,player)
                board.pop()

    return queue

    
def play_card(card,pgn) :
    root = card[0]
    node = card[1]
    status = node.status
    player = not pgn.board().turn

    # front of card
    front = root.variations[0]
    if (status == NEW) :
        print("\nNEW : this is a position you haven't seen before\n")
    if (status == FIRST_STEP or status == SECOND_STEP) :
        print("\nLEARNING : this is a position you're currently learning\n")
    if (status == REVIEW) :
        print("\nRECALL : this is a position you've learned, due for recall\n")

    print_board(front.board(),player)
    if (status == NEW) :
        print("\nGuess the move..")
    else :
        print("\nRecall the move..")
    print(".. then hit [enter] or 'c' to close")
    command = input("\n:")
    if (command == "c") :
        return "CLOSE"

    # back of card
    back = front.variations[0]
    clear()    
    print("Solution:")
    print_board(back.board(),player)

    if (status == NEW) :
        print("\nHit [enter] to continue.")
        input("\n\n:")
    else :
        print("\n'h' hard    [enter] ok    'e' easy\n")
        command = input("\n:")
   
    while (True) :
        if (command == "e") :
            return "EASY"
        if (command == "h") :
            return "HARD"
        if (command == "") :
            return "OK"
        if (command == "c") :
            return "CLOSE"
        command = input(":")        
        
def handle_card_result(result,card,queue,pgn) :

    root = card[0]
    node = card[1]
    status = node.status
    
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    if (status == "NEW") :
        node.status = "FIRST_STEP"
        increase = int(round(3 * random.random()))
        offset = min(1 + increase,len(queue))
        queue.insert(offset,card)
                    
    elif (status == "FIRST_STEP") :
        if (result == "EASY") :
            node.status = "REVIEW"
            node.last_date = today
            node.due_date = tomorrow
            pgn.new_remaining -= 1
        elif (result == "OK") :
            node.status = "SECOND_STEP"
            increase = int(round(3 * random.random()))
            offset = min(6 + increase,len(queue))
            queue.insert(offset,card)
        elif (result == "HARD") :
            node.status = "FIRST_STEP"            
            increase = int(round(3 * random.random()))
            offset = min(1 + increase,len(queue))
            queue.insert(offset,card)

    elif (status == "SECOND_STEP") :
        if (result == "EASY") :
            node.status = "REVIEW"
            node.last_date = today
            node.due_date = today + datetime.timedelta(days=3)
            pgn.new_remaining -= 1
        elif (result == "OK") :
            node.status = "REVIEW"
            node.last_date = today
            node.due_date = tomorrow
            pgn.new_remaining -= 1            
        elif (result == "HARD") :
            node.status = "FIRST_STEP"            
            increase = int(round(3 * random.random()))
            offset = min(1 + increase,len(queue))
            queue.insert(offset,card)
            
    elif (status == "REVIEW") :
        previous_gap = (node.due_date - node.last_date).days

        if (result == "HARD") :
            node.status = "FIRST_STEP"
            offset = min(2,len(queue))
            queue.insert(offset,card)
            pgn.new_remaining -= 1                        

        else :
            if (result == "EASY") :
                multiplier = 3 + random.random()
            else :
                multiplier = 2 + random.random()
            new_gap = int(round(previous_gap * multiplier))
            node.status = "REVIEW"
            node.last_date = today
            node.due_date = today + datetime.timedelta(days=new_gap)

##############
# backing-up #
##############

#def backup_collections() :

# read last access date, and create file if needed
# if last access precedes

###############
# entry point #
###############

#backup_collections()
main_menu()

