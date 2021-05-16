from typing import Any, Type, Union

from django.db import models

from .enums import Enum, IntEnum

_StrOrEnum = Union[str, Type[Enum]]

class EnumFieldMixin:
    def __init__(self, enum: _StrOrEnum, **kwargs: Any) -> None: ...

class EnumField(EnumFieldMixin, models.CharField[Enum, Any]): ...
class EnumIntegerField(EnumFieldMixin, models.IntegerField[IntEnum, Any]): ...
