import abc
from typing import Union, Optional, Any

from zugzwang.group import Group, Tabia
#from zugzwang.training import TrainingSpec

# TODO: fix typing entailing circular import
#SceneResult = Union[Group, Tabia, TrainingSpec]
SceneResult = Any

class Scene(abc.ABC):
    @abc.abstractmethod
    def go() -> Optional[SceneResult]:
        pass
