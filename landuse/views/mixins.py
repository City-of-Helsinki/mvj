from typing import TYPE_CHECKING, Any, ClassVar

from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import BasePagination, LimitOffsetPagination
from rest_framework.request import Request

if TYPE_CHECKING:
    from rest_framework.views import APIView

    _MixinBase = APIView
else:
    _MixinBase = object


class LandUseApiEnabledFlagMixin(_MixinBase):
    """
    Intent is to block views unless `FLAG_LANDUSE_API_ENABLED is True`.
    """

    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        """Runs before any method invocation to check if the Land Use API is enabled."""
        if getattr(settings, "FLAG_LANDUSE_API_ENABLED", False) is not True:
            raise PermissionDenied

        super().initial(request, *args, **kwargs)


class LandUseLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100


class LandUsePaginationMixin:
    pagination_class: ClassVar[type[BasePagination] | None] = (
        LandUseLimitOffsetPagination
    )
    default_limit = 100
