from django.contrib import auth
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class UsersPermissions(APIView):
    permission_classes = (IsAuthenticated,)

    def get_view_name(self):
        return _("Users permissions")

    def get(self, request, format=None, contract_id=None, file_id=None):
        if request.user.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = set()
            for backend in auth.get_backends():
                if hasattr(backend, "get_all_permissions"):
                    permissions.update(backend._get_user_permissions(request.user))
                    permissions.update(backend._get_group_permissions(request.user))

        groups = [g.name for g in request.user.groups.all()]

        return Response(
            {
                "groups": groups,
                "permissions": [{
                    "name": p.name,
                    "codename": p.codename
                } for p in permissions]
            }
        )
