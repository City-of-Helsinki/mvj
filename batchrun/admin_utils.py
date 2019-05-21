from datetime import datetime
from typing import Optional, Type

from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(
            self,
            request: HttpRequest,
            obj: Optional[Model] = None,
    ) -> bool:
        return False

    def has_change_permission(
            self,
            request: HttpRequest,
            obj: Optional[Model] = None,
    ) -> bool:
        return False

    def has_delete_permission(
            self,
            request: HttpRequest,
            obj: Optional[Model] = None,
    ) -> bool:
        return False


class PreciseTimeFormatter:
    _format_string = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, model: Type[Model], field_name: str) -> None:
        self._model = model
        self._field_name = field_name
        self._field = model._meta.get_field(field_name)
        self.admin_order_field = field_name

    @property
    def short_description(self) -> str:
        return str(self._field.verbose_name)

    def __call__(self, obj: Model) -> Optional[str]:
        value = getattr(obj, self._field_name)
        if value is None:
            return value
        assert isinstance(value, datetime)
        return value.strftime(self._format_string)
