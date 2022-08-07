import pytest
import os

from zugzwang.chapter import ZugChapter

# define the path to the example category, which holds the example chapters
EXAMPLE_CATEGORY_PATH = os.path.join(
    os.getcwd(), 'TestCollections/ExampleCollection/ExampleCategory'
)


# TODO
# Figure out how to unit test this class.
# Is it sufficiently high-level that these tests can be considered automated
# integration tests? They will likely need to open and save files, and check their
# content. So we need to figure out how to make these processes backwards compatible,
# as the .chp standard format will certainly expand.

class TestZugChapter:

    def test_init(self):
        # The constructor is sufficiently complex that it requires a unit test.
        pass
    
    def test_update_stats(self):
        pass

    def test_save(self):
        pass


class TestZugChapterGetSolutionNodes():

    @pytest.mark.parametrize(
        'chp_filename', ['linear.chp', 'linear-hanging-problem.chp']
    )
    def test_linear(self, chp_filename):
        # tests a chapter with no branching and five solutions, ending with or without
        # a 'hanging problem'; i.e. a problem that is not followed by a solution
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        chapter = ZugChapter(chp_filepath)
        game = chapter._game
        
        node = game
        expected_solution_nodes = []
        for _ in range(5):
            node = node.variations[0]
            node = node.variations[0]
            expected_solution_nodes.append(node)

        assert chapter._get_solution_nodes() == expected_solution_nodes

    @pytest.mark.parametrize(
        'chp_filename', ['branching.chp','branching-hanging-problems.chp']
    )
    def test_branching(self, chp_filename ):
        # tests a PGN with branching, three moves deep and no unreachable solutions
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, chp_filename)
        root = ZugChapter(chp_filepath).root
        game = root.game

        # the easist strategy to grab the expected solution nodes is just nesting
        # for loops to cover three-move depth
        expected_solution_nodes = []    
        for problem in game.variations:
            for solution in problem.variations:
                expected_solution_nodes.append(solution)
                for problem in solution.variations:
                    for solution in problem.variations:
                        expected_solution_nodes.append(solution)

        assert root.solution_nodes() == expected_solution_nodes

    def test_unreachable(self):
        # tests a PGN with unreachable solutions
        # for throroughness, the PGN also has branching and hanging problems
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

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

        assert root.solution_nodes() == expected_solution_nodes

    def test_basic_blunder(self):
        # tests a PGN with single blunder
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game

        # there are only two solutions, so grab them explicity
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])
    
        assert root.solution_nodes() == expected_solution_nodes


    def test_blunders_and_branching(self):
        # tests a PGN with branching and single blunders, i.e. the opponent does not
        # blunder back in the refutation
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunders-and-branching.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
    
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
    
        assert root.solution_nodes() == expected_solution_nodes

    def test_hanging_blunders(self):
        # tests a PGN with hanging blunders, i.e. the blunder has no refutation
        # we also test blunders which aren't qualified by a proper solution
        # the distinction is important; a blunder is a problem, but it is also
        # an error; solutions to both exist, but their perspectives are different
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'hanging-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
    
        expected_solution_nodes = []
        problem = game.variations[0]
        solution = problem.variations[0]
        expected_solution_nodes.append(solution)
        problem = solution.variations[0]
        blunder = problem.variations[0]
        expected_solution_nodes.append(blunder.variations[0])    
    
        assert root.solution_nodes() == expected_solution_nodes

    def test_blunder_and_unreachable(self):
        # tests a PGN with a node that has a solution, a blunder and an unreachable
        # candidate
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'blunder-and-unreachable.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
        
        expected_solution_nodes = []
        problem = game.variations[0]
        expected_solution_nodes.append(problem.variations[0])
        blunder = problem.variations[1]
        expected_solution_nodes.append(blunder.variations[0])    

        assert root.solution_nodes() == expected_solution_nodes

    def test_double_blunders(self):
        # tests a PGN in which the opponent blunders back in the refutation
        # hence the perspective will reverse twice in one line
        chp_filepath = os.path.join(EXAMPLE_CATEGORY_PATH, 'double-blunders.chp')
        root = ZugChapter(chp_filepath).root
        game = root.game
        
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

        assert root.solution_nodes() == expected_solution_nodes

    def test_white_from_starting_position(self):
        # tests a PGN in which the training player has the move in the root position.
        # the other case is tested implicitly in several tests above
        chp_filepath = os.path.join(
            EXAMPLE_CATEGORY_PATH,
            'white-from-starting-position.chp'
        )
        root = ZugChapter(chp_filepath).root
        game = root.game

        expected_solution_nodes = []
        solution = game.variations[0]
        expected_solution_nodes.append(solution)
        for problem in solution.variations:
            expected_solution_nodes.append(problem.variations[0])

        assert root.solution_nodes() == expected_solution_nodes




        
