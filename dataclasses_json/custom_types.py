from typing import Any
from typing import Callable
from typing import List
from typing import Tuple
from typing import TypeVar
from typing import Union

__all_ = ["T", "A", "B", "C", "Fields", "Json", "Convert"]

T = TypeVar("T")
A = TypeVar("A", bound="DataClassJsonMixin")
B = TypeVar("B")
C = TypeVar("C")

Json = Union[dict, list, str, int, float, bool, None]
Convert = Callable[[T], C]
Fields = List[Tuple[str, Any]]
