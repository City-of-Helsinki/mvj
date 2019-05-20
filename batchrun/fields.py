from typing import Any, Dict, Tuple

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _

from .intset import IntegerSetSpecifier


class IntegerSetSpecifierField(models.CharField):  # type: ignore
    def __init__(
            self,
            *,
            value_range: Tuple[int, int],
            default: str = '*',
            **kwargs: Any,
    ) -> None:
        assert isinstance(value_range, tuple)
        assert len(value_range) == 2
        assert all(isinstance(x, int) for x in value_range)
        self.value_range: Tuple[int, int] = value_range
        kwargs.setdefault('max_length', 200)
        kwargs['validators'] = list(kwargs.get('validators', [])) + [
            self._validate_spec_syntax,
        ]
        super().__init__(default=default, **kwargs)

    def deconstruct(self) -> Tuple[str, str, Tuple[Any], Dict[str, Any]]:
        (name, path, args, kwargs) = super().deconstruct()

        kwargs['value_range'] = self.value_range
        kwargs['validators'] = [
            x for x in kwargs.get('validators', [])
            if x != self._validate_spec_syntax]

        default_kwargs = [
            ('max_length', 200),
            ('default', '*'),
            ('validators', []),
        ]
        for (name, default) in default_kwargs:
            if kwargs.get(name) == default:
                del kwargs[name]

        return (name, path, args, kwargs)

    def to_intset(self, value: object) -> IntegerSetSpecifier:
        return IntegerSetSpecifier(str(value), *self.value_range)

    def _validate_spec_syntax(self, value: object) -> None:
        try:
            self.to_intset(value)
        except ValueError:
            raise ValidationError(
                _('Invalid integer set specifier'), code='invalid-spec')
