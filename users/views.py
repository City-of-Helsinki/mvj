from django.contrib import auth
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSetMixin

from leasing.serializers.service_unit import ServiceUnitSerializer


class UsersPermissions(APIView):
    permission_classes = (IsAuthenticated,)
    excluded_permission_apps = ("landuse",)

    def get_view_name(self):
        return _("Users permissions")

    def get(self, request, format=None):
        if request.user.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = set()
            for backend in auth.get_backends():
                if hasattr(backend, "get_all_permissions"):
                    permissions.update(backend._get_user_permissions(request.user))
                    permissions.update(backend._get_group_permissions(request.user))

        groups = [g.name for g in request.user.groups.all()]
        service_units = request.user.service_units.all()
        service_units_serializer = ServiceUnitSerializer(service_units, many=True)

        return Response(
            {
                "groups": groups,
                "service_units": service_units_serializer.data,
                "permissions": [
                    {
                        "app": p.content_type.app_label,
                        "name": p.name,
                        "codename": p.codename,
                    }
                    for p in permissions
                    if p.content_type.app_label not in self.excluded_permission_apps
                ],
            }
        )


class LandUseUsersPermissions(ViewSetMixin, UsersPermissions):
    excluded_permission_apps = ()

    def list(self, request, format=None):
        permissions = super().get(request, format)
        permissions.data["permissions"] = [
            permission
            for permission in permissions.data["permissions"]
            if permission["app"] == "landuse"
        ]
        return permissions
