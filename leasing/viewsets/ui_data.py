from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from leasing.models import UiData
from leasing.permissions import IsSameUser, MvjDjangoModelPermissions
from leasing.serializers.ui_data import UiDataCreateUpdateSerializer, UiDataSerializer

from .utils import AtomicTransactionModelViewSet


class CanEditGlobalUiData(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'user') or obj.user:
            return True

        return request.user.has_perm('leasing.edit_global_ui_data')


class UiDataViewSet(AtomicTransactionModelViewSet):
    serializer_class = UiDataSerializer
    permission_classes = (IsAuthenticated, MvjDjangoModelPermissions, IsSameUser, CanEditGlobalUiData)

    def get_queryset(self):
        return UiData.objects.filter(
            Q(user__isnull=True) | Q(user=self.request.user)
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return UiDataCreateUpdateSerializer

        return UiDataSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.has_perm('leasing.edit_global_ui_data'):
            if 'user' not in request.data:
                request.data['user'] = request.user.id

            if not request.data.get('user'):
                raise PermissionDenied(_("Can't create global ui data"))

        if request.data.get('user') and request.data.get('user') != request.user.id:
            raise PermissionDenied(_("Can't create other users ui data"))

        return super().create(request, *args, **kwargs)
