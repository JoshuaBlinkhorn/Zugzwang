import os

from zugzwang.chapter import ZugChapter
from zugzwang.stats import ZugStats

class ZugGroup:

    def __init__(self, path, child_type):
        self._path = path
        self._child_type = child_type
        self.children = self._get_children()
        self.stats = self._get_stats()
        self.name = path.split('/')[-1]
        self.menu_type = None
        
    def _get_children(self):
        children = []
        for child_name in sorted(os.listdir(self._path)):
            child_path = os.path.join(self._path, child_name)
            children.append(self._child_type(child_path))
        return children

    def _get_stats(self):
        stats = ZugStats()
        for child in self._get_children():
            stats = stats + child.stats
        return stats


class ZugUserData(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugCollection)


class ZugCollection(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugCategory)


class ZugCategory(ZugGroup):
    def __init__(self, path):
        super().__init__(path, ZugChapter)
