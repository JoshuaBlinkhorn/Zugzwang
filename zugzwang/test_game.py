import pytest
import mock

from game import (
    ZugRootData,
    ZugRoot,
    ZugSolutionData,
    ZugSolution,
)


class TestZugRootData():

    def test_from_comment():
        pass

    def test_make_comment():
        pass


class TestZugRoot():

    def test_decrement_learning_remaining():
        ZugRoot().decrement_learning_remaining()

    def test_has_learning_capacity():
        ZugRoot().has_learning_capacity()

    def test_update_game_comment():
        ZugRoot().update_game_comment()
        
    def test_update_learning_remaining():
        ZugRoot().update_learning_remaining()

    def test_solution_nodes():
        
    def test_from_naked_game():
        pass

    def test_reset_training_data():
        pass

    def test_update_learning_remaining():
        pass


class TestZugSolutionData():

    def test_from_comment():
        pass

    def test_make_comment():
        pass
    
    def test_update():
        pass


class TestZugSolution():

    def test_update_node_comment():
        pass

    def test_learned():
        pass

    def test_recalled():
        pass

    def test_forgotten():
        pass


    
