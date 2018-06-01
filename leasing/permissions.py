from rest_framework.permissions import BasePermission


class HasViewLeasePermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.has_perm('leasing.view_lease')
