from datetime import datetime
from functools import update_wrapper
from typing import Any, List, Optional, Type, TypeVar

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Field, Model
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import path, reverse
from django.urls.resolvers import URLPattern
from django.utils import timezone
from django.utils.html import format_html

from batchrun.models import JobRunLog

AnyModel = TypeVar("AnyModel", bound=Model)


class ReadOnlyAdmin(admin.ModelAdmin[AnyModel]):
    def has_add_permission(
        self, request: HttpRequest, obj: Optional[Model] = None
    ) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[Model] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[Model] = None
    ) -> bool:
        return False


class PreciseTimeFormatter:
    _format_string = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, model: Type[Model], field_name: str) -> None:
        self._model = model
        self._field_name = field_name
        self._field = model._meta.get_field(field_name)
        self.admin_order_field = field_name

    @property
    def short_description(self) -> str:
        if isinstance(self._field, Field):
            return str(self._field.verbose_name)
        return ""

    def __call__(self, obj: Model) -> Optional[str]:
        value = getattr(obj, self._field_name)
        if value is None:
            return value
        assert isinstance(value, datetime)
        return timezone.localtime(value).strftime(self._format_string)


class WithDownloadableContent(admin.ModelAdmin[JobRunLog]):
    @property
    def download_content_url_name(self) -> str:
        meta = self.model._meta
        return f"{meta.app_label}_{meta.model_name}_download_content"

    def get_urls(self) -> List[URLPattern]:
        def wrap(view: Any) -> Any:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self  # type: ignore
            return update_wrapper(wrapper, view)

        return [
            path(
                "<path:object_id>/download-content/",
                wrap(self.download_content_view),
                name=self.download_content_url_name,
            )
        ] + super().get_urls()

    def download_content(self, obj: Any) -> str:
        site_name = self.admin_site.name
        url_name = self.download_content_url_name
        return format_html(
            '<a href="{}">{}</a>',
            reverse(f"{site_name}:{url_name}", args=[obj.pk]),
            "Download content",
        )

    download_content.short_description = "Download content"  # type: ignore

    def download_content_view(
        self, request: HttpRequest, object_id: int
    ) -> HttpResponse:
        try:
            obj = self.model.objects.get(pk=object_id)
        except (ObjectDoesNotExist, ValueError):
            raise Http404
        filename = self.get_downloadable_content_filename(obj)
        response = HttpResponse(content_type="application/text-plain")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(self.get_downloadable_content(obj))
        return response

    def get_downloadable_content(self, obj: Any) -> str:
        return repr(obj)

    def get_downloadable_content_filename(self, obj: Any) -> str:
        return "content.txt"
