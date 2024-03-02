from __future__ import annotations

import os
from typing import List, Union
from pathlib import Path
import abc

import chess

from zugzwang.game import ZugSolution
from zugzwang.stats import ZugStats
from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools


class Item(abc.ABC):

    def __init__(self, path: Path):
        self._path = path
        self._stats = self._generate_stats()

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def stats(self) -> ZugStats:
        return self._stats

    @abc.abstractmethod
    def lines(self) -> List[Line]:
        pass

    @abc.abstractmethod
    def solutions(self) -> List[chess.pgn.Node]:
        pass

    @abc.abstractmethod
    def tabias(self) -> List[Tabia]:
        pass

    @abc.abstractmethod
    def _generate_stats(self) -> ZugStats:
        pass

    def update_stats(self) -> None:
        self._stats = self._generate_stats()


class Tabia(Item):

    def __init__(self, path: Path):
        self._path = path
        
        # collect root
        with open(path) as fp:
            game: chess.Game = chess.pgn.read_game(fp)
            self._root = ZugRoot(game)
                
        # form solution set
        self._solutions = ZugChessTools.get_solution_nodes(
            self._root.game_node,
            self._root.data.perspective
        )

        # update root and stats
        self._root.update()
        self._stats = self._generate_stats()

    @property
    def root(self) -> ZugRoot:
        return self._root
        
    def solutions(self) -> List[ZugSolution]:
        return self._solutions

    def lines(self) -> List[List[chess.pgn.GameNode]]:
        return ZugChessTools.get_lines(
            self._root.game_node,
            self._root.data.perspective
        )

    def tabias(self) -> List[Tabia]:
        return [self]
    
    def save(self):
        with open(self._path, 'w') as fp:
            print(self._root.game_node, file=fp)

    def _generate_stats(self):
        stats = ZugStats()
        stats.total = len(self._solutions)
        return stats


class Group(Item):
    def __init__(self, path: Path):
        self._path = path
        self._children = self._generate_children()                
        self._stats = self._generate_stats()

    @property
    def children(self) -> List[Union[Group, Tabia]]:
        return self._children

    def tabias(self) -> List[Tabia]:
        return [tabia for item in self._children for tabia in item.tabias()]

    def lines(self) -> List[ZugLine]:
        return [line for item in self._children for line in item.lines()]

    def solutions(self) -> List[chess.pgn.Node]:
        return [solution for item in self._children for solution in item.solutions()]

    def _generate_children(self) -> List[Item]:
        names: List[str] = self._filter(sorted(os.listdir(self._path)))
        children: List[Item] = []

        for name in names:
            path = self._path / name
            cls = Group if path.is_dir() else Tabia
            children.append(cls(path))

        return children

    def _filter(self, children: List[str]) -> List[str]:
        return [child for child in children if not self._is_excluded(child)]

    def _is_excluded(self, filename: str):
        # TODO: get the stubs out of the collections and clean this up
        return filename.startswith(".") or "backup" in filename or "STUB" in filename

    def _generate_stats(self):
        stats = ZugStats()
        for child in self._children:
            stats = stats + child.stats
        return stats
