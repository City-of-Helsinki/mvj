from rest_framework import permissions


class MvjDjangoModelPermissions(permissions.DjangoModelPermissions):
    """Customized Django REST Framework DjangoModelPermissions
    class that includes checking for the "view" permissions too.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class PerMethodPermission(permissions.BasePermission):
    """Per method permission check

    Permission where the required permissions can be configured
    per method. Returns True if no permissions are configured.
    If multiple permissions listed, the user must have all of
    the permissions."""

    perms_map = {
        'GET': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
        'OPTIONS': [],
    }

    def get_required_permissions(self, method, view):
        """Get required permissions for method and view combo

        Given method and view, return the list of permission
        codes that the user is required to have.
        """
        perms_map = self.perms_map.copy()

        if hasattr(view, 'perms_map'):
            perms_map.update(view.perms_map)

        if method not in perms_map:
            return []

        return perms_map[method]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        required_perms = self.get_required_permissions(request.method, view)

        return request.user.has_perms(required_perms)
