from django.test import override_settings
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from landuse.views.mixins import LandUseApiEnabledFlagMixin


class FeatureFlaggedViewSet(LandUseApiEnabledFlagMixin, viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


@override_settings(FLAG_LANDUSE_API_ENABLED=False)
def test_viewset_is_disabled_when_landuse_flag_is_false():
    request = APIRequestFactory().get("/")
    view = FeatureFlaggedViewSet.as_view({"get": "list"})

    response = view(request)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(FLAG_LANDUSE_API_ENABLED=True)
def test_viewset_is_enabled_when_landuse_flag_is_true():
    request = APIRequestFactory().get("/")
    view = FeatureFlaggedViewSet.as_view({"get": "list"})

    response = view(request)

    assert response.status_code == status.HTTP_204_NO_CONTENT
