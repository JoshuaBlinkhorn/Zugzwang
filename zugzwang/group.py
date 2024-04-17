from __future__ import annotations

import os
from typing import List, Union
import pathlib
import abc
import datetime
import dataclasses
import json
import enum
import chess
import random

from zugzwang.stats import ZugStats
from zugzwang.tools import ZugChessTools, ZugJsonTools
from zugzwang.dates import ZugDates
from zugzwang import dates


class Status(str, enum.Enum):
    LEARNED = "LEARNED"
    UNLEARNED = "UNLEARNED"


class Result(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class MetadataError(Exception):
    pass


class IOError(Exception):
    pass


@dataclasses.dataclass
class Metadata:
    perspective: chess.Color = chess.WHITE
    status: Status = Status.UNLEARNED
    last_study_date: Optional[datetime.date] = None
    due_date: Optional[datetime.date] = None
    successes: int = 0
    failures: int = 0
    recall_radius: int = 3
    recall_factor: float = 2.0
    recall_max: int = 365

    @classmethod
    def from_json(cls, json_str: str) -> Metadata:
        try:
            dict_ = json.loads(json_str)
        except json.decoder.JSONDecodeError as exc:
            raise MetadataError()
        dict_ = {key: cls._inverse(val) for key, val in dict_.items()}
        return cls(**dict_)

    def as_json(self) -> str:
        string = json.dumps(
            dataclasses.asdict(self),
            default=self._default,
            indent=2,
        )
        return string + "\n"

    def success(self):
        self.status = Status.LEARNED
        self.successes += 1
        self.last_study_date = dates.today()
        self.due_date = self._due_date()

    def failure(self):
        self.last_study_date = dates.today()
        self.due_date = ZugDates.tomorrow()
        self.failures += 1

    @staticmethod
    def _default(value: Any) -> Any:
        # convert datetime.date to ISO date string
        # leave all other values unchanged
        if isinstance(value, datetime.date):
            return value.isoformat()
        raise TypeError("Cannot serialise python object in JSON.")

    @classmethod
    def _inverse(cls, value: Any) -> Any:
        if isinstance(value, str) and cls._is_date(value):
            return cls._to_date(value)
        return value

    @staticmethod
    def _is_date(string: str) -> bool:
        if not len(parts := string.split("-")) == 3:
            return False
        if not all(
            [
                len(string) == 10,
                len(parts[0]) == 4,
                len(parts[1]) == 2,
                len(parts[2]) == 2,
                *[part.isdigit() for part in parts],
            ]
        ):
            return False
        return True

    @staticmethod
    def _to_date(date: str):
        year, month, day = tuple(date.split("-"))
        return datetime.date(int(year), int(month), int(day))

    def _due_date(self) -> datetime.date:
        if self.last_study_date is None:
            raise ValueError("Cannot calculate due_date without last_study_date")

        if self.due_date is None:
            return dates.tomorrow()

        # calculate the diff based on recall factor and radius
        previous_diff = (self.due_date - self.last_study_date).days
        absolute_diff = int(previous_diff * self.recall_factor)
        offset = random.randint(-self.recall_radius, self.recall_radius)

        # impose minimum and maximum values
        diff = max(1, min(absolute_diff + offset, self.recall_max))
        return dates.today() + datetime.timedelta(days=diff)


class Item(abc.ABC):
    def __init__(
        self,
        name: str,
        parent: Optional[Group] = None,
    ):
        self._name = name
        self._parent = parent
        self._stats = self._generate_stats()

    @property
    def name(self) -> str:
        return self._name

    @property
    def directory(self) -> pathlib.Path:
        return self._dir

    @property
    def parent(self) -> Optional[Group]:
        return self._parent

    @property
    def stats(self) -> ZugStats:
        if self._stats is None:
            self._stats = self._generate_stats()
        return self._stats

    @abc.abstractmethod
    def tabias(self) -> Generator[Tabia, None, None]:
        pass

    @abc.abstractmethod
    def _generate_stats(self) -> ZugStats:
        pass

    def update_stats(self) -> None:
        self._stats = self._generate_stats()


class Group(Item):
    def __init__(
        self,
        name: str,
        parent: Optional[Group] = None,
    ):
        self._name: str = name
        self._parent: Optional[Group] = parent
        self._children: List[Item] = []
        self._stats = None

    def tabias(self) -> Generator[Tabia, None, None]:
        def gen():
            for child in self._children:
                yield from child.tabias()

        return gen()

    def _generate_stats(self):
        stats = ZugStats()
        for child in self._children:
            stats = stats + child.stats
        return stats

    @property
    def children(self) -> List[Item]:
        return self._children

    def add_child(self, child: Item) -> None:
        self._children.append(child)


class Tabia(Item):
    def __init__(
        self,
        name: str,
        parent: Group,
        io_manager: IOManager,
    ):
        self._name = name
        self._parent = parent
        self._game = io_manager.read(self)
        self._metadata = io_manager.read_meta(self) or self._default_metadata()
        self._stats = None

    @property
    def game(self) -> chess.GameNode:
        return self._game

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> Metadata:
        return self._metadata

    def flip_perspective(self):
        self._metadata.perspective = not self._metadata.perspective

    def tabias(self) -> Generator[Tabia, None, None]:
        def gen():
            yield self

        return gen()

    def solutions(self) -> List[chess.pgn.ChildNode]:
        return ZugChessTools.get_solution_nodes(
            self._game,
            self._metadata.perspective,
        )

    def lines(self) -> List[List[chess.pgn.GameNode]]:
        return ZugChessTools.get_lines(self._game, self._metadata.perspective)

    def is_learned(self):
        return self._metadata.status == Status.LEARNED

    def is_due(self):
        return self.is_learned() and self._metadata.due_date <= dates.today()

    def record_attempt(self, result: Result) -> None:
        if result == Result.SUCCESS:
            self._metadata.success()
        elif result == Result.FAILURE:
            self._metadata.failure()

    def _generate_stats(self) -> ZugStats:
        stats = ZugStats()
        stats.total = len(self.solutions())
        return stats

    def _default_metadata(self) -> Metadata:
        if self._game.headers["White"] == "p":
            perspective = chess.WHITE
        elif self._game.headers["Black"] == "p":
            perspective = chess.BLACK
        else:
            perspective = not self._game.board().turn
        return Metadata(perspective=perspective)


class IOManager(abc.ABC):
    @abc.abstractmethod
    def read_meta(self, tabia: Tabia) -> str:
        pass

    @abc.abstractmethod
    def write_meta(self, tabia: Tabia) -> None:
        pass

    @abc.abstractmethod
    def read(self, tabia: Tabia) -> chess.pgn.Game:
        pass


class DefaultIOManager(IOManager):
    def __init__(self):
        self._groups: Dict[Group, pathlib.Path] = {}

    def read_meta(self, tabia: Tabia) -> Optional[Metadata]:
        meta_path = self._meta_path(tabia)
        if not meta_path.exists():
            return None
        with open(meta_path) as fp:
            data = fp.read()
        try:
            meta = Metadata.from_json(data)
        except MetadataError as exc:
            raise IOError(f"Cannot read metadata for {tabia.name}") from exc
        return meta

    def write_meta(self, tabia: Tabia) -> None:
        with open(self._meta_path(tabia), "w") as fp:
            fp.write(tabia.metadata.as_json())

    def read(self, tabia: Tabia) -> chess.pgn.Game:
        with open(self._pgn_path(tabia)) as fp:
            game = chess.pgn.read_game(fp)
        return game

    def register_group(self, group: Group, path: pathlib.Path):
        self._groups[group] = path

    def _meta_path(self, tabia: Tabia) -> pathlib.Path:
        return self._groups[tabia.parent] / (tabia.name + ".json")

    def _pgn_path(self, tabia: Tabia) -> pathlib.Path:
        return self._groups[tabia.parent] / (tabia.name + ".pgn")
