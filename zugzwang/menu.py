from typing import Union, List
import abc
import enum

from zugzwang.group import Item, Group, Tabia
from zugzwang.training import (
    Trainer,
    TrainingOptions,
    TrainingMode,
)


class Status(str, enum.Enum):
    EXIT = "EXIT"
    REDRAW = "REDRAW"

class Menu(abc.ABC):

    @classmethod
    def _clear_screen(cls):
        print('\n' * 100)
    
    def display(self):
        self._print_content()
        while self._handle_input(self._prompt()) != Status.EXIT:
            self._print_content()

    def _print_content(self) -> None:
        self._clear_screen()
        for line in self._get_content():
            print(line)

    def _handle_input(self, input_: str) -> Status:
        if not self._validate(input_):
            return Status.REDRAW
        return self._handle(input_)

    def _prompt(self) -> str:
        return input(":")
    
    # TODO: these methods shoulddo the printing
    # The concrete classes should just pass in text
    @abc.abstractmethod
    def _get_content(self) -> List[str]:
        pass

    @abc.abstractmethod
    def _validate(self, input_: str) -> bool:
        pass

    @abc.abstractmethod
    def _handle(self, input_: str) -> Status:
        pass

class GroupMenu(Menu):

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
    
    @classmethod
    def _represents_int(cls, value):
        try:
            int(value)
        except:
            return False
        return True

    def __init__(self, group: Group):
        self._group = group

    def _get_content(self) -> List[str]:
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
            'b  - go back',
        ]
    
    def _validate(self, input_) -> bool:
        if self._represents_int(input_):
            return int(input_) - 1 in range(0, len(self._group.children))
        if input_ in ['p', 'l', 'b']:
            return True
        return False
    
    def _handle(self, input_):
        if self._represents_int(input_):
            index = int(input_) - 1
            item = self._group.children[index]
            cls = GroupMenu if isinstance(item, Group) else TabiaMenu
            cls(item).display()
            # TODO: this might be handled by the trainer
            self._group.update_stats()

        elif input_ == 'p':
            options = TrainingOptions(mode=TrainingMode.POSITIONS)
            tabias = self._group.tabias()
            Trainer(options).train(tabias)

        elif input_ == 'l':
            options = TrainingOptions(mode=TrainingMode.LINES)            
            tabias = self._group.tabias()
            Trainer(options).train(tabias)

        elif input_ == 'b':
            return Status.EXIT


class TabiaMenu(Menu):

    _col_width = 20
    
    def __init__(self, tabia: Tabia):
        self._tabia = tabia

    def _get_content(self) -> List[str]:
        return [
            " ".join(['Tabia'.ljust(self._col_width), self._tabia.name]),
            "",
            " ".join(['New '.ljust(self._col_width), str(self._tabia.stats.new)]),
            " ".join(['Due'.ljust(self._col_width), str(self._tabia.stats.due)]),
            " ".join(['Learned'.ljust(self._col_width), str(self._tabia.stats.learned)]),
            " ".join(['Total'.ljust(self._col_width), str(self._tabia.stats.total)]),   
            "",
            'p - position-based training',
            'l - line-based training',
            'b - go back',
            "",
        ]

    def _validate(self, input_):
        return input_ in ['p', 'l', 'b']

    def _handle(self, input_):
        if input_ == 'p':
            training_units = self._group.tabias()
            Trainer(training_units).train()
            return Status.REDRAW

        elif input_ == 'l':
            training_units = self._group.lines()
            Trainer(training_units).train()
            return Status.REDRAW

        elif input_ == 'b':
            return Status.EXIT


        
