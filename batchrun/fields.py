from typing import Any, Dict, Sequence, Tuple

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.json import JSONField
from django.utils.translation import gettext as _

from .intset import IntegerSetSpecifier


class IntegerSetSpecifierField(models.CharField):  # type: ignore
    def __init__(
        self, *, value_range: Tuple[int, int], default: str = "*", **kwargs: Any
    ) -> None:
        assert isinstance(value_range, tuple)
        assert len(value_range) == 2
        assert all(isinstance(x, int) for x in value_range)
        self.value_range: Tuple[int, int] = value_range
        kwargs.setdefault("max_length", 200)
        kwargs["validators"] = list(kwargs.get("validators", [])) + [
            self._validate_spec_syntax
        ]
        super().__init__(default=default, **kwargs)

    def deconstruct(self) -> Tuple[str, str, Sequence[Any], Dict[str, Any]]:
        (name, path, args, kwargs) = super().deconstruct()

        kwargs["value_range"] = self.value_range
        kwargs["validators"] = [
            x for x in kwargs.get("validators", []) if x != self._validate_spec_syntax
        ]

        default_kwargs = [("max_length", 200), ("default", "*"), ("validators", [])]
        for kwarg_name, default in default_kwargs:
            if kwargs.get(kwarg_name) == default:
                del kwargs[kwarg_name]

        return (name, path, args, kwargs)

    def to_intset(self, value: object) -> IntegerSetSpecifier:
        return IntegerSetSpecifier(str(value), *self.value_range)

    def _validate_spec_syntax(self, value: object) -> None:
        try:
            self.to_intset(value)
        except ValueError:
            raise ValidationError(
                _("Invalid integer set specifier"), code="invalid-spec"
            )


class TextJSONField(JSONField):
    def db_type(self, connection: Any) -> str:
        return "json"

    def from_db_value(
        self, value: Any, expression: Any, connection: Any
    ) -> dict[str, Any] | None | Any:
        """
        This is a workaround to make this field work with Django.
        Changing the db_type to "json" causes the issue that this
        field can't even be accessed and raises a TypeError.
        """
        # Seems like setting db_type to "json" gives back value that is a dict.
        if isinstance(value, dict):
            return value

        value = super().from_db_value(value, expression, connection)  # type: ignore[misc]
        return value
