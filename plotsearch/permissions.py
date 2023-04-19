from leasing.permissions import PerMethodPermission


class AreaSearchAttachmentPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.area_search.user == request.user:
            return True
        return super().has_object_permission(request, view, obj)
