from django.conf import settings
from rest_framework.exceptions import PermissionDenied


class LandUseApiEnabledFlagMixin:
    """
    Intent is to block views unless `FLAG_LANDUSE_API_ENABLED is True`.
    """

    def initial(self, request, *args, **kwargs):
        """Runs before any method invocation to check if the Land Use API is enabled."""
        if getattr(settings, "FLAG_LANDUSE_API_ENABLED", False) is not True:
            raise PermissionDenied

        super().initial(request, *args, **kwargs)
