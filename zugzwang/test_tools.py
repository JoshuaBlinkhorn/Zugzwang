import pytest
import datetime
import chess.pgn
import os

from zugzwang.tools import (
    ZugStringTools,
    ZugStringDelimiterError,
    ZugJsonDecodeError,
    ZugJsonEncodeError,    
    ZugJsonTools,
    ZugChessTools,    
)
from zugzwang.constants import ZugColours

# define the path to the example category, which holds the example chapters
TEST_CATEGORY_PATH = os.path.join(
    os.getcwd(), 'TestCollections/ExampleCollection/ToolsTestCHPs'
)

class TestZugJsonTools():
    """Unit tests for ZugJsonTools."""

    @pytest.mark.parametrize(
        'data_dict, expected_string',
        [
            pytest.param(
                {},
                '{}',
                id='empty dict'
            ),
            pytest.param(
                {
                    'integer': 0,
                    'float': 0.0,
                    'string': '0.0',
                    'date': datetime.date(year=2000, month=1, day=1),
                },
                (
                    '{'
                    '"integer": 0, '
                    '"float": 0.0, '
                    '"string": "0.0", '
                    '"date": "2000-01-01"'
                    '}'
                ),
                id='all types'
            ),
        ]
    )
    def test_encode(self, data_dict, expected_string):
        """Encodes a dictionary as a string, writing datetime.dates in ISO format."""
        assert ZugJsonTools.encode(data_dict) == expected_string

    @pytest.mark.parametrize(
        'invalid_object',
        [
            pytest.param([], id="list"),
            pytest.param(tuple(), id="tuple"),
            pytest.param("foobar", id="string"),
            pytest.param(0, id="numeric"),
        ]
    )
    def test_encode_invalid_object(self, invalid_object):
        with pytest.raises(ZugJsonEncodeError):
            ZugJsonTools.encode(invalid_object)

    @pytest.mark.parametrize(
        'string, expected_dict',
        [
            pytest.param(
                '{}',
                {},
                id='empty dict'
            ),
            pytest.param(
                (
                    '{'
                    '"integer": 0, '
                    '"float": 0.0, '
                    '"string": "0.0", '
                    '"date": "2000-01-01"'
                    '}'
                ),
                {
                    'integer': 0,
                    'float': 0.0,
                    'string': '0.0',
                    'date': datetime.date(year=2000, month=1, day=1),
                },
                id='all types'
            ),
        ]
    )
    def test_decode(self, string, expected_dict):
        """
        Decodes a string into a dict, converting ISO format dates to datetime.date.
        """
        assert ZugJsonTools.decode(string) == expected_dict

    @pytest.mark.parametrize(
        'invalid_string',
        [
            pytest.param('asdfadh', id='gobbledygook'),
            pytest.param('[]', id='square braces'),
            pytest.param('()', id='round braces'),          
            pytest.param('{"integer"}', id='invalid curly braces'),
        ]
    )
    def test_decode_invalid_string(self, invalid_string):
        with pytest.raises(ZugJsonDecodeError):
            ZugJsonTools.decode(invalid_string)


class TestZugStringTools:
    """Unit tests for ZugStringTools."""
    
    @pytest.mark.parametrize(
        'string, expected_output',
        [
            pytest.param(
                '{}',
                '[]',
                id='empty',
            ),
            pytest.param(
                '{foobar}',
                '[foobar]',
                id='non-empty non-nested',
            ),
            pytest.param(
                '{foobar{barfoo}foobar}',
                '[foobar[barfoo]foobar]',
                id='non-empty nested',
            ),
        ]
    )
    def test_to_square_braces(self, string, expected_output):
        """Cruly braces are made square if the string is valid."""
        assert ZugStringTools.to_square_braces(string) == expected_output
    
    @pytest.mark.parametrize(
        'invalid_string',
        [
            pytest.param('', id='empty',),
            pytest.param('{', id='left only'),
            pytest.param('}', id='right only'),
            pytest.param('!{}!', id='flanked'),            
        ]
    )
    def test_to_square_braces_bad_delimiters(self, invalid_string):
        """An exception is raised if the string is not delimited with curly braces."""
        with pytest.raises(ZugStringDelimiterError):
            ZugStringTools.to_square_braces(invalid_string)
    
            
    @pytest.mark.parametrize(
        'string, expected_output',
        [
            pytest.param(
                '[]',
                '{}',
                id='empty',
            ),
            pytest.param(
                '[foobar]',
                '{foobar}',
                id='non-empty non-nested',
            ),
            pytest.param(
                '[foobar[barfoo]foobar]',
                '{foobar{barfoo}foobar}',
                id='non-empty nested',
            ),
        ]
    )
    def test_to_curly_braces(self, string, expected_output):
        """Cruly braces are made square if the string is valid."""
        assert ZugStringTools.to_curly_braces(string) == expected_output
    
    @pytest.mark.parametrize(
        'invalid_string',
        [
            pytest.param('', id='empty',),
            pytest.param('[', id='left only'),
            pytest.param(']', id='right only'),
            pytest.param('![]!', id='flanked'),            
        ]
    )
    def test_to_curly_braces_bad_delimiters(self, invalid_string):
        """An exception is raised if the string is not delimited with curly braces."""
        with pytest.raises(ZugStringDelimiterError):
            ZugStringTools.to_curly_braces(invalid_string)
    
            
class TestGetSolutionNodes():

    @pytest.mark.parametrize(
        'chp_filename', ['linear.chp', 'linear-hanging-problem.chp']
    )
    def test_linear(self, chp_filename):
        # tests a chapter with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, chp_filename)
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)
        
        node = game
        expected_solution_nodes = []
        for _ in range(5):
            node = node.variations[0]
            node = node.variations[0]
            expected_solution_nodes.append(node)

        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    @pytest.mark.parametrize(
        'chp_filename', ['branching.chp','branching-hanging-problems.chp']
    )
    def test_branching(self, chp_filename ):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, chp_filename)
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover three-move depth
        expected_solution_nodes = []    
        for problem in game.variations:
            for solution in problem.variations:
                expected_solution_nodes.append(solution)
                for problem in solution.variations:
                    for solution in problem.variations:
                        expected_solution_nodes.append(solution)

        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_unreachable(self):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'unreachable.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover two-move depth, and searching only the first variation
        # of problems
        expected_solution_nodes = []
        for problem in game.variations:
            solution = problem.variations[0]
            expected_solution_nodes.append(solution)
            for problem in solution.variations:
                solution = problem.variations[0]
                expected_solution_nodes.append(solution)

        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_basic_blunder(self):
        # tests a PGN with single blunder
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunder.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)

        # there are only two solutions, so grab them explicity
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])
    
        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_blunders_and_branching(self):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunders-and-branching.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]    
        expected_solution_nodes.append(solution)
        blunder = problem.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)

        problem = game.variations[1]    
        solution = problem.variations[0]    
        expected_solution_nodes.append(solution)
        blunder = problem.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)
        for problem in refutation.variations:
            expected_solution_nodes.append(problem.variations[0])
    
        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_hanging_blunders(self):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'hanging-blunders.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]
        expected_solution_nodes.append(solution)
        problem = solution.variations[0]
        blunder = problem.variations[0]
        expected_solution_nodes.append(blunder.variations[0])    
    
        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_blunder_and_unreachable(self):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunder-and-unreachable.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)
        
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])    

        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_double_blunders(self):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'double-blunders.chp')
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)
        
        expected_solution_nodes = []
        expected_solution_nodes.append(game.variations[0])
        blunder = game.variations[1]
        refutation = blunder.variations[0]
        expected_solution_nodes.append(refutation)
        problem = refutation.variations[0]
        return_blunder = problem.variations[0]
        refutation = return_blunder.variations[0]            
        expected_solution_nodes.append(refutation)
        for problem in refutation.variations:
            expected_solution_nodes.append(problem.variations[0])

        perspective = ZugColours.BLACK
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes

    def test_white_from_starting_position(self):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        chp_filepath = os.path.join(
            TEST_CATEGORY_PATH,
            'white-from-starting-position.chp'
        )
        with open(chp_filepath) as chapter_file:
            game = chess.pgn.read_game(chapter_file)

        expected_solution_nodes = []
        solution = game.variations[0]
        expected_solution_nodes.append(solution)
        for problem in solution.variations:
            expected_solution_nodes.append(problem.variations[0])

        perspective = ZugColours.WHITE
        solution_nodes = ZugChessTools.get_solution_nodes(game, perspective)
        assert solution_nodes == expected_solution_nodes


class TestZugToolsGetLines():

    @pytest.mark.parametrize(
        'chp_filename',
        ['linear.chp','linear-hanging-problem.chp'],
    )
    def test_linear(self, chp_filename):
        # tests a PGN with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, chp_filename)
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        line = list(game.mainline())[:10]
        expected_lines = [line]            

        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    @pytest.mark.parametrize(
        'chp_filename',
        ['branching.chp','branching-hanging-problems.chp']
    )
    def test_branching(self, chp_filename):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, chp_filename)
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)
        
        # there is no simpler way to do this than construct the lines manually.
        main = list(game.mainline())[0:4]
        line_a = main[:]
        variation = main[-3].variations[1]
        line_b = main[:-2] + [variation, variation.variations[0]]
        variation = game.variations[1]
        line_c = [variation] + list(variation.mainline())[:3]
        variation = line_c[-3].variations[1]
        line_d = line_c[:2] + [variation, variation.variations[0]]        
        expected_lines = [line_a, line_b, line_c, line_d]

        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines
        
    def test_unreachable(self):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'unreachable.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # there is only one line, the main line
        expected_lines = [list(game.mainline())]

        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_basic_blunder(self):
        # tests a PGN with single blunder
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunder.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # there two lines, the main line and the blunder line
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        expected_lines = [line_a, line_b]
        
        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_blunders_and_branching(self):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunders-and-branching.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # again, there is no clever way, we just build the lines
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        variation = game.variations[1]
        line_c = [variation, variation.variations[0]]
        blunder = variation.variations[1]
        line_d = [blunder] + list(blunder.mainline())
        variation = line_d[-3].variations[1]
        line_e = line_d[:2] + [variation, variation.variations[0]]
        expected_lines = [line_a, line_b, line_c, line_d, line_e]        
        
        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_hanging_blunders(self):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'hanging-blunders.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # there are just two lines
        main = list(game.mainline())
        line_a = main[:2]
        line_b = main[-2:]
        expected_lines = [line_a, line_b]

        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_blunder_and_unreachable(self):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'blunder-and-unreachable.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # there two lines, the main line and the blunder line
        line_a = list(game.mainline())
        blunder = line_a[0].variations[1]
        line_b = [blunder, blunder.variations[0]]
        expected_lines = [line_a, line_b]
        
        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_double_blunders(self):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        chp_filepath = os.path.join(TEST_CATEGORY_PATH, 'double-blunders.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # there are four lines
        line_a = [game, game.variations[0]]
        blunder = game.variations[1]
        line_b = [blunder, blunder.variations[0]]
        blunder = list(blunder.mainline())[2]
        line_c = [blunder] + list(blunder.mainline())
        variation = line_c[-3].variations[1]
        line_d = line_c[:2] + [variation, variation.variations[0]]
        expected_lines = [line_a, line_b, line_c, line_d]
        
        perspective = ZugColours.BLACK
        assert ZugChessTools.get_lines(game, perspective) == expected_lines

    def test_white_from_starting_position(self):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        chp_filepath = os.path.join(
            TEST_CATEGORY_PATH,
            'white-from-starting-position.chp')
        with open(chp_filepath) as chp_file:
            game = chess.pgn.read_game(chp_file)

        # here there are four lines, but we can exploit the structure or the PGN
        # with a for loop
        mainline = [game] + list(game.mainline())
        expected_lines = [mainline]
        junction = mainline[1]
        for variation in junction.variations[1:]:
            expected_lines.append(mainline[:2] + [variation, variation.variations[0]])

        perspective = ZugColours.WHITE
        assert ZugChessTools.get_lines(game, perspective) == expected_lines
