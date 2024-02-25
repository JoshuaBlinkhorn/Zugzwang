from typing import Union
from zugzwang.group import ZugGroup
from zugzwang.chapter import ZugChapter
from zugzwang.training import ZugPositionTrainer, ZugLineTrainer
from zugzwang.line_trainer import LineTrainer

class ZugMenu:

    @classmethod
    def _clear_screen(cls):
        print('\n' * 100)
    
    def display(self):
        self._clear_screen()
        self._print_content()
        while self._handle_input(self._prompt()) is None:
            self._clear_screen()
            self._print_content()

    def _print_content(self):
        print('default menu content\n')

    def _prompt(self):
        print('default menu prompt')
        print("type 'b' to go back")        
        return input(':')

    def _handle_input(self, user_input):
        if not self._validate_input(user_input):
            return None
        return self._handle_good_input(user_input)

    def _validate_input(self, user_input):
        return user_input == 'b'

    def _handle_good_input(self):
        return True

class ZugChapterMenu(ZugMenu):

    _col_width = 20
    
    def __init__(self, chapter: ZugChapter):
        self._chapter = chapter

    def _print_taxonomy(self):
        print('Collection'.ljust(self._col_width), self._chapter.collection)
        print('Category'.ljust(self._col_width), self._chapter.category)
        print('Chapter'.ljust(self._col_width), self._chapter.name)                
        
    def _print_stats(self):
        print('New '.ljust(self._col_width), self._chapter.stats.new)
        print('Due'.ljust(self._col_width), self._chapter.stats.due)
        print('Learned'.ljust(self._col_width), self._chapter.stats.learned)
        print('Total'.ljust(self._col_width), self._chapter.stats.total)        
        
    def _print_content(self):
        self._print_taxonomy()
        print('')
        self._print_stats()        
        print('')

    def _prompt(self):
        print('p - position-based training')
        print('l - line-based training')
        print('b - go back\n')
        return input(':')

    def _validate_input(self, user_input):
        return user_input in 'plb'

    def _handle_good_input(self, user_input):
        if user_input == 'b':
            return True
        if user_input == 'p':
            self._chapter.train_positions()
            return None
        if user_input == 'l':
            self._chapter.train_lines()            
            return None

        
class ZugGroupMenu(ZugMenu):

    _child_name = 'CHILD_NAME'
    _child_menu_type = None

    def __init__(self, group: ZugGroup):
        self._group = group

    @classmethod
    def _header(cls):
        return {
            'item_id': ('ID', 3),
            'coverage': ('COV.', 5),
            'training_available': ('', 2),
            'item_name': (cls._child_name, 30),
            'new': ('NEW', 4),
            'due': ('DUE', 4),
            'learned': ('LRN', 4),
            'total': ('ALL', 4),                                   
        }
        
    @classmethod
    def _represents_int(cls, value):
        try:
            int(value)
        except:
            return False
        return True

    @classmethod
    def _print_header(cls):
        for header, spacing in cls._header().values():
            print(header.ljust(spacing), end='')
        print('\n')
    
    @classmethod
    def _print_row(cls, index: int, child: Union[ZugGroup, ZugChapter]):
        stats = child.stats
        coverage = (stats.learned * 100) // stats.total if stats.total > 0 else 0
        row = {
            'item_id': str(index + 1),
            'coverage': '{}% '.format(coverage),
            'training_available': '*' if stats.new + stats.learned > 0 else '',
            'item_name': child.name,
            'new': str(stats.new),
            'due': str(stats.due),
            'learned': str(stats.learned),
            'total': str(stats.total),   
        }
        for field, string in row.items():
            _, spacing = cls._header()[field]
            if field == 'coverage':
                print(string[:spacing].rjust(spacing), end='')
                continue
            print(string.ljust(spacing), end='')
        print('')

    def _print_content(self):
        self._print_header()
        for index, child in enumerate(self._group.children):
            self._print_row(index, child)
        print('')

    def _prompt(self):
        print('id - select item')
        print('b  - go back\n')
        return input(':')

    def _handle_input(self, user_input):
        num_items = len(self._group.children)
        if self._represents_int(user_input) and int(user_input) in range(1, num_items+1):
            item_index = int(user_input) - 1
            next_item = self._group.children[item_index]
            self._load_next_menu(next_item)
            return None
        if user_input == 'b':
            return True
        return None

    def _load_next_menu(self, item):
        self._child_menu_type(item).display()
        self._group.update_stats()


class ZugCategoryMenu(ZugGroupMenu):
    _child_name = 'CHAPTER'
    _child_menu_type = ZugChapterMenu

    def _prompt(self):
        print('id - select item')
        print('p - position-based training')
        print('l - line-based training')
        print('b  - go back\n')
        return input(':')

    def _handle_input(self, user_input):
        num_items = len(self._group.children)
        if self._represents_int(user_input) and int(user_input) in range(1, num_items+1):
            item_index = int(user_input) - 1
            next_item = self._group.children[item_index]
            self._load_next_menu(next_item)
            return None
        if user_input == 'p':
            for chapter in self._group.children:
                chapter.train_positions()
            return None
        if user_input == 'l':
            self._train_lines()
            return None
        if user_input == 'b':
            return True
        return None

    def _train_lines(self):
        lines = [
            line
            for chapter in self._group.children
            for line in chapter.lines
        ]
        LineTrainer(lines).train()

class ZugCollectionMenu(ZugGroupMenu):
    _child_name = 'CATEGORY'
    _child_menu_type = ZugCategoryMenu


class ZugMainMenu(ZugGroupMenu):
    _child_name = 'COLLECTION'
    _child_menu_type = ZugCollectionMenu
        

