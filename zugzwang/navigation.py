import os

from zugzwang.chapter import ZugChapter
from zugzwang.stats import ZugStats

class Category:

    def __init__(self, category_path):
        self._category_path = category_path
        self._chapters = self._get_chapters()
        self.stats = self._get_stats()

    def _get_chapters(self):
        chapters = []
        for chapter_name in os.listdir(self._category_path):
            chapter_path = os.path.join(self._category_path, chapter_name)
            chapters.append(ZugChapter(chapter_path))
        return chapters

    def _get_stats(self):
        stats = ZugStats()
        for chapter in self._get_chapters():
            stats = stats + chapter.stats
        return stats
    
class Collection:

    def __init__(self, collection_path):
        self._collection_path = collection_path
        self._categories = self._get_categories()
        self.stats = self._get_stats()

    def _get_categories(self):
        categories = []
        for category_name in os.listdir(self._collection_path):
            category_path = os.path.join(self._collection_path, category_name)
            categories.append(Category(category_path))
        return categories
            
    def _get_stats(self):
        stats = ZugStats()
        for category in self._get_categories():
            stats = stats + category.stats
        return stats
    
class MainMenu:

    def __init__(self, collections_dir_path):
        self._collections_dir_path = collections_dir_path
        self._collections = self._get_collections()
    
    def _get_collections(self):
        collections = []
        for collection_name in os.listdir(self._collections_dir_path):
            collection_path = os.path.join(self._collections_dir_path, collection_name)
            collections.append(Collection(collection_path))
        return collections

    def display(self):
        for collection in self._collections:
            print(collection.stats)
        
