import abc
import json
import pathlib
from typing import TYPE_CHECKING

import chess.pgn

from zugzwang.group import Group, Tabia
from zugzwang.config import DATA_DIR

class IOManager(abc.ABC):
    @abc.abstractmethod
    def read_meta(self, tabia: Tabia) -> str:
        pass

    @abc.abstractmethod
    def write_meta(self, tabia: Tabia, metadata: str) -> None:
        pass

    @abc.abstractmethod
    def read(self, tabia: Tabia) -> chess.pgn.Game:
        pass


class DefaultIOManager(IOManager):

    def __init__(self):
        self._groups: Dict[Group, pathlib.Path] = {}

    def register_group(self, group: Group, path: pathlib.Path):
        self._groups[group] = path
    
    def read_meta(self, tabia: Tabia) -> str:
        with open(self._meta_path(tabia)) as fp:
            string = fp.read()
        return string

    def write_meta(self, tabia: Tabia, metadata: str) -> None:
        with open(self._meta_path(), "w") as fp:
            fp.write(metadata)

    def read(self, tabia: Tabia) -> chess.pgn.Game:
        with open(self._pgn_path(tabia)) as fp:
            game = chess.pgn.read_game(fp)
        return game

    def _meta_path(self, tabia: Tabia) -> pathlib.Path:
        return self._groups[tabia.parent] / (tabia.name + ".json")
    
    def _pgn_path(self, tabia: Tabia) -> pathlib.Path:
        return self._groups[tabia.parent] / (tabia.name + ".pgn")
