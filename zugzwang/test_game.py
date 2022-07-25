import pytest
import mock
import datetime
import json

from zugzwang.game import (
    ZugRootData,
    ZugRoot,
    ZugSolutionData,
    ZugSolution,
)
from zugzwang.constants import ZugColours

# fix a mock epoch and dates relative to it
EPOCH = datetime.date(2000,1,1)
def epoch_shift(shift: int):
    return EPOCH + datetime.timedelta(days=shift)

# fix root data values, different to defaults
LEARNING_REMAINING = 15
LEARNING_LIMIT = 20
RECALL_FACTOR = 2.5
RECALL_RADIUS = 5
RECALL_MAX = 500


@pytest.fixture
def root_data():
    return ZugRootData(
        perspective = ZugColours.WHITE,
        last_access = EPOCH,
        learning_remaining = LEARNING_REMAINING,
        learning_limit = LEARNING_LIMIT,
        recall_factor = RECALL_FACTOR,
        recall_radius = RECALL_RADIUS,
        recall_max = RECALL_MAX,        
    )


@pytest.fixture
def root_data_comment():
    return (
        '{'
        '"perspective": true, '
        '"last_access": "2000-01-01", '
        '"learning_remaining": 15, '
        '"learning_limit": 20, '
        '"recall_factor": 2.5, '
        '"recall_radius": 5, '
        '"recall_max": 500'
        '}'
    )


class TestZugRootData():

    def test_from_comment(self, root_data_comment, root_data):
        assert ZugRootData.from_comment(root_data_comment) == root_data

    def test_make_comment(self, root_data, root_data_comment):
        assert root_data.make_comment() == root_data_comment


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
        pass
        
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


    
