from __future__ import annotations
from typing import Dict, Any
import os

from zugzwang.group import ZugUserData
from zugzwang.display import ZugDisplay
from zugzwang.scene import (
    ZugScene,
    ZugSceneView,
    ZugSceneModel,    
)
from zugzwang.view import (
    ZugTextView,
    ZugViewGroup,
)

class ZugTableScene(ZugScene):
    _CHILD_SCENE_TYPE = None

    def __init__(self, display: ZugDisplay, group: ZugGroup):
        model = ZugTableModel(group)    
        width = display.get_screen().get_width()
        height = display.get_screen().get_height()
        view = ZugTableView(width, height)

        super().__init__(display, model, view)

    def _left_click_registered(self, view_id: str):
        print("CLICKED:", view_id)
        if view_id.startswith('table-item-'):
            path = view_id.split('.')
            index = int(path[0].split('-')[-1])
            field = path[1]
            if field == 'edit':
                group = self._model.get_children()[index]
                self._load_next_scene(group)

    def _load_next_scene(self, group: ZugGroup):
        scene = self._CHILD_SCENE_TYPE(self._display, group)
        self._display.push_scene(scene)


class ZugTableView(ZugSceneView):

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

    def update(self, model: ZugTableModel):
        # Updating here actually has to build the collection row views, because
        # their number is dynamic
        left = 10
        top = 120
        height = ZugRowView.get_height()
        data = model.table_data()

        for index, row in enumerate(data):
            item_id = f'table-item-{index}'            
            pos = (left, top + (index * height))
            self._add_item(item_id, pos, ZugRowView(row))


class ZugTableModel(ZugSceneModel):
    def __init__(self, group: ZugGroup):
        self._group = group

    def table_data(self):
        data = []        
        for item in self._group.children:
            stats = item.stats
            coverage = (stats.learned * 100) // stats.total if stats.total > 0 else 0
            training_available = True if stats.new + stats.due > 0 else False            
            data.append(
                {
                    'name': item.name,
                    'coverage': coverage,
                    'training_available': training_available,
                    'new': stats.new,
                    'due': stats.due,
                    'learned': stats.learned,
                    'total': stats.total,
                }
            )
        return data

    def get_children(self):
        return self._group.children

        
class ZugRowView(ZugViewGroup):
    _HEIGHT = 40
    _WIDTH = 1000
    
    def __init__(self, row: Dict[str, Any]):
        super().__init__()

        # coverage
        item_id = "coverage"
        position = (0, 0)
        self._add_item(item_id, position, ZugCoverageView())

        # name
        item_id = "name"
        position = (position[0] + ZugCoverageView.get_width(), 0)
        self._add_item(item_id, position, ZugItemNameView())        
        
        # new
        item_id = "new"
        position = (position[0] + ZugItemNameView.get_width(), 0)
        self._add_item(item_id, position, ZugNumberView())

        # due
        item_id = "due"
        position = (position[0] + ZugNumberView.get_width(), 0)
        self._add_item(item_id, position, ZugNumberView())

        # learned
        item_id = "learned"
        position = (position[0] + ZugNumberView.get_width(), 0)
        self._add_item(item_id, position, ZugNumberView())

        # total
        item_id = "total"
        position = (position[0] + ZugNumberView.get_width(), 0)
        self._add_item(item_id, position, ZugNumberView())

        # position training
        item_id = "position_training"
        position = (position[0] + ZugNumberView.get_width(), 0)
        self._add_item(item_id, position, ZugPositionTrainingButton())

        # tree training
        item_id = "tree_training"
        position = (position[0] + ZugPositionTrainingButton.get_width(), 0)
        self._add_item(item_id, position, ZugTreeTrainingButton())

        # edit
        item_id = "edit"
        position = (position[0] + ZugTreeTrainingButton.get_width(), 0)
        self._add_item(item_id, position, ZugEditButton())

        self.update(row)

    def update(self, row: Dict[str: Any]):
        # remaining captions
        for item in ("coverage", "name", "new", "due", "learned", "total"):
            self._items[item].set_caption(str(row[item]))



class ZugCoverageView(ZugTextView):
    _WIDTH = 50
    _HEIGHT = ZugRowView.get_height()

    def set_caption(self, caption: str):
        self._caption = caption + '%'


class ZugItemNameView(ZugTextView):
    _WIDTH = 600
    _HEIGHT = ZugRowView.get_height()


class ZugNumberView(ZugTextView):
    _WIDTH = 50
    _HEIGHT = ZugRowView.get_height()


class ZugPositionTrainingButton(ZugTextView):
    _WIDTH = 50
    _HEIGHT = ZugRowView.get_height()

    def __init__(self):
        super().__init__(caption='P')


class ZugTreeTrainingButton(ZugTextView):
    _WIDTH = 50
    _HEIGHT = ZugRowView.get_height()
    
    def __init__(self):
        super().__init__(caption='T')


class ZugEditButton(ZugTextView):
    _WIDTH = 50
    _HEIGHT = ZugRowView.get_height()
    
    def __init__(self):
        super().__init__(caption='E')


class DuplicateViewIdError(ValueError):
    pass

        
class ZugTreeEditor(ZugScene):
    def __init__(self, display: ZugDisplay, chapter: ZugChapter):
        pass


class ZugCategoryScene(ZugTableScene):
    _CHILD_SCENE_TYPE = ZugTreeEditor

    # these functions don't really need overriding
    # the only issue is that a category is not a group
    # so the type hints and nomenclature are wrong
    # but we'd get the same behaviour if we didn't override
    def _left_click_registered(self, view_id: str):
        if view_id.startswith('table-item-'):
            path = view_id.split('.')
            index = int(path[0].split('-')[-1])
            field = path[1]
            if field == 'edit':
                chapter = self._model.get_children()[index]
                self._load_next_scene(chapter)

    def _load_next_scene(self, chapter: ZugChapter):
        scene = self._CHILD_SCENE_TYPE(self._display, chapter)
        self._display.push_scene(scene)


class ZugCollectionScene(ZugTableScene):
    _CHILD_SCENE_TYPE = ZugCategoryScene


class ZugInitialScene(ZugTableScene):
    _CHILD_SCENE_TYPE = ZugCategoryScene

