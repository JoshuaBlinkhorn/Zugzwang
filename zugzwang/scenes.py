import abc
from typing import Union, Optional, Any

from zugzwang.group import Group, Tabia, IOManager
#from zugzwang.training import TrainingSpec

# TODO: fix typing entailing circular import
#SceneResult = Union[Group, Tabia, TrainingSpec]
SceneResult = Any

class Scene(abc.ABC):
    @abc.abstractmethod
    def go(self, io_manager: IOManager) -> Optional[SceneResult]:
        pass

    @abc.abstractmethod
    def kill(self, io_manager: IOManager) -> None:
        pass
