import abc
from typing import Optional, List, Union

from zugzwang.scenes import Scene, SceneResult
from zugzwang.training import TrainingMode, TrainingOptions, TrainingSpec
from zugzwang.group import Item, Tabia, Group


# TODO: Tabia menu scene accessing protected Tabia property
# either configure access propery or figure out a better way
# to set the perspective

_training_mode_map = {
    'l': TrainingMode.LINES,
    'p': TrainingMode.PROBLEMS,
    't': TrainingMode.TABIAS,
    's': TrainingMode.SCHEDULED,           
}

class MenuScene(Scene):

    @abc.abstractmethod
    def _content(self) -> List[str]:
        pass

    @abc.abstractmethod
    def _validate(self, input_: str) -> Optional[str]:
        pass

    @abc.abstractmethod
    def _handle(self, input_: str) -> Optional[Union[SceneResult, bool]]:
        pass

    def go(self) -> SceneResult:
        result = False
        while result is False:
            self._print_content()
            while (input_ := self._validate(self._prompt())) is None:
                self._print_content()
            result = self._handle(input_)
        return result

    def _print_content(self) -> None:
        self._clear_screen()
        for line in self._content():
            print(line)

    def _prompt(self) -> str:
        return input(":")
    
    @classmethod
    def _clear_screen(cls):
        print('\n' * 100)
    
    
class TabiaScene(MenuScene):

    _col_width = 20
    
    def __init__(self, tabia: Tabia):
        self._tabia = tabia

    def _content(self) -> List[str]:
        return [
            " ".join(['Tabia'.ljust(self._col_width), self._tabia.name]),
            " ".join([
                'Perspective'.ljust(self._col_width),
                "White" if self._tabia._metadata.perspective else "Black"
            ]),          
            "",
            " ".join(['New '.ljust(self._col_width), str(self._tabia.stats.new)]),
            " ".join(['Due'.ljust(self._col_width), str(self._tabia.stats.due)]),
            " ".join(['Learned'.ljust(self._col_width), str(self._tabia.stats.learned)]),
            " ".join(['Total'.ljust(self._col_width), str(self._tabia.stats.total)]),   
            "",
            'p - position-based training',
            'l - line-based training',
            't - tabia-based training',
            'f - flip perspective',            
            'b - go back',
            "",
        ]

    def _validate(self, input_):
        valid_chars = ['p', 'l', 't', 'f', 'b']
        return input_ if input_ in valid_chars  else None

    def _handle(self, input_):

        if input_ in ['p', 'l', 't']:
            mode = _training_mode_map[input_]
            options = TrainingOptions(mode=mode)
            return TrainingSpec(self._tabia, options)

        elif input_ == 'f':
            self._tabia._metadata.perspective = not self._tabia._metadata.perspective
            return False
            
        elif input_ == 'b':
            return None


class GroupScene(MenuScene):

    _learning_limit = 1
    _table_schema = {
        'item_id': ('ID', 3),
        'coverage': ('COV.', 5),
        'training_available': ('', 2),
        'item_name': ('ITEM', 30),
        'new': ('NEW', 6),
        'due': ('DUE', 6),
        'learned': ('LRN', 6),
        'total': ('ALL', 6),                                   
    }
    
    def __init__(self, group: Group):
        self._group = group

    def _content(self) -> List[str]:
        return [
            self._get_header(),
            *self._get_table(),
            "",
            *self._get_choices(),
            "",
        ]

    def _get_header(self) -> str:
        return "".join(
            [
                header.ljust(spacing)
                for header, spacing in self._table_schema.values()
            ]
        )

    def _get_table(self) -> List[str]:
        return [
            self._get_row(index + 1, child)
            for index, child in enumerate(self._group.children)
        ]

    def _get_row(self, index: int, item: Item) -> str:
        stats = item.stats
        coverage = (stats.learned * 100) // stats.total if stats.total > 0 else 0
        row = {
            'item_id': str(index),
            'coverage': str(coverage) + '% ',
            'training_available': '*' if stats.new + stats.learned > 0 else '',
            'item_name': item.name,
            'new': str(stats.new),
            'due': str(stats.due),
            'learned': str(stats.learned),
            'total': str(stats.total),   
        }

        row_str = ""
        for field, string in row.items():
            _, spacing = self._table_schema[field]
            if field == 'coverage':
                row_str += string.rjust(spacing)
                continue
            row_str += string.ljust(spacing)

        return row_str

    def _get_choices(self) -> List[str]:
        return [
            'id - select item',
            'p  - position-based training',
            'l  - line-based training',
            't  - tabia-based training',
            's  - scheduled training',            
            'b  - go back',
        ]
    
    def _validate(self, input_) -> Optional[str]:
        if input_ in ['p', 'l', 't', 's', 'b']:
            return input_
        if not self._represents_int(input_):
            return None
        val = int(input_) - 1 
        return input_ if val in range(0, len(self._group.children)) else None

    def _handle(self, input_) -> Optional[SceneResult]:
        if self._represents_int(input_):
            index = int(input_) - 1
            return self._group.children[index]

        elif input_ in ['p', 'l', 't', 's']:
            mode = _training_mode_map[input_]
            options = TrainingOptions(mode=mode)
            return TrainingSpec(self._group, options)

        elif input_ == 'b':
            return None

    @classmethod
    def _represents_int(cls, value):
        try:
            int(value)
        except:
            return False
        return True



    
