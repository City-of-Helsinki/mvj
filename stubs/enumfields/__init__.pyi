import enum
from typing import Any, Sequence, Tuple, Type, Union

from django.db import models


class Enum(enum.Enum):
    @classmethod
    def choices(cls) -> Sequence[Tuple[str, str]]: ...

    def __str__(self) -> str: ...


_StrOrEnum = Union[str, Type[Enum]]


class EnumFieldMixin:
    ...


class EnumField(EnumFieldMixin, models.CharField[Enum, Any]):
    def __init__(self, enum: _StrOrEnum, **kwargs: Any) -> None: ...
