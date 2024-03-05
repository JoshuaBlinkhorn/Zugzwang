from __future__ import annotations

import os
from typing import List, Union
from pathlib import Path
import abc
import datetime
import dataclasses
import json
import enum
import chess

from zugzwang.game import ZugSolution
from zugzwang.stats import ZugStats
from zugzwang.game import ZugRoot, ZugSolution
from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools, ZugJsonTools
from zugzwang.dates import ZugDates

class TabiaStatus(str, enum.Enum):
    LEARNED = 'LEARNED'
    UNLEARNED = 'UNLEARNED'


class TabiaResult(str, enum.Enum):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'


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



class TabiaMetadata:
    def __init__(
            self,
            status: TabiaStatus = TabiaStatus.UNLEARNED,
            last_study_date: datetime.date = None,
            due_date: datetime.date = None,
            successes: int = 0,
            failures: int = 0,
            recall_radius: int = 3, 
            recall_factor: float = 2.0,
            recall_max: int = 365,
            
    ):
        self.status = status
        self.last_study_date = (
            ZugDates.yesterday() if last_study_date is None else last_study_date
        )
        self.due_date = ZugDates.yesterday() if due_date is None else due_date
        self.successes = successes
        self.failures = failures
        self.recall_radius = recall_radius
        self.recall_factor = recall_factor
        self.recall_max = recall_max

    def as_dict(self):
        return {
            "status": self.status,
            "last_study_date": self.last_study_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "successes": self.successes,
            "failure": self.failures,
            "recall_radius": self.recall_radius,
            "recall_factor": self.recall_factor,
            "recall_max": self.recall_max,
        }

    @classmethod
    def from_dict(cls, dict_: Dict):
        dict_["last_study_date"] = _to_date(dict_["last_study_date"])
        dict_["due_date"] = _to_date(dict_["due_date"])
        return(cls(**dict_))
        
    def learned(self):
        self.status = TabiaStatus.LEARNED
        self.last_study_date = ZugDates.today()
        self.due_date = ZugDates.tomorrow(),
        self.successes += 1
        
    def successful_recall(self):
        due_date = ZugDates.due_date(
            self.last_study_date,
            self.due_date,
            self.recall_radius,
            self.recall_factor,
            self.recall_max,            
        )
        self.successes += 1
        self.last_study_date = ZugDates.today(),
        self.due_date = due_date

    def failed_recall(self):
        self.last_study_date = ZugDates.today()
        self.due_date = ZugDates.tomorrow(),
        self.failuers += 1

    @staticmethod
    def _to_date(date: str):
        year, month, day = tuple(date.split('-'))
        return datetime.date(int(year), int(month), int(day))
        
class Tabia(Item):

    def __init__(self, path: Path):
        self._path = path
        self._meta_path = self._meta_path()
        self._metadata = self._get_metadata()

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


    def _meta_path(self):        
        dir_ = self._path.parent
        meta_name = self._path.name[:4] + ".txt"
        return dir_ / meta_name
        
    def _get_metadata(self):
        if not self._meta_path.exists():
            return TabiaMetadata()
        with open(self._meta_path) as fp:
            data = json.load(fp)
        return TabiaMetadata.from_dict(data)
        
        
    @property
    def stats(self) -> Stats:
        return self._stats
        
    @property
    def root(self) -> ZugRoot:
        return self._root
    
    def solutions(self) -> List[chess.pgn.ChildNode]:
        return self._solutions

    def lines(self) -> List[List[chess.pgn.GameNode]]:
        return ZugChessTools.get_lines(
            self._root.game_node,
            self._root.data.perspective
        )

    def tabias(self) -> List[Tabia]:
        return [self]

    def is_learned(self):
        return self._metadata.status == TabiaStatus.LEARNED
        
    def is_due(self):
        return self.is_learned() and self._metadata.due_date <= ZugDates.today()
    
    def record_attempt(self, result: TabiaResult) -> None:
        if not self.is_learned():
            self._metadata.learned()
        else:
            if result == TabiaResult.SUCCESS:
                self._metadata.successful_recall()
            elif result == TabiaResult.FAILURE:
                self._metadata.failed_recall()                
        self._write_metadata()

    def _write_metadata(self):
        with open(self._meta_path, 'w', encoding='utf-8') as fp:
            json.dump(self._metadata.as_dict(), fp, indent=4)
            
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
    def children(self) -> List[Item]:
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
        return filename.startswith(".") or filename.endswith(".json")

    def _generate_stats(self):
        stats = ZugStats()
        for child in self._children:
            stats = stats + child.stats
        return stats
