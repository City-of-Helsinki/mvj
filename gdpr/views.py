from helsinki_gdpr.views import GDPRAPIView
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class AmrPermission(BasePermission):
    """Authentication Method Reference (amr)"""

    def has_permission(self, request: Request, _view: "MvjGDPRAPIView") -> bool:
        amrs: list[str] = request.auth.data.get("amr", [])
        allowed_amr = "suomi_fi"
        has_allowed_amr = allowed_amr in amrs
        return has_allowed_amr


class MvjGDPRAPIView(GDPRAPIView):
    permission_classes = GDPRAPIView.permission_classes + [AmrPermission]
