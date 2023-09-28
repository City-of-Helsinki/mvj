from leasing.permissions import PerMethodPermission
from plotsearch.models import PlotSearch
from users.models import User


class AreaSearchAttachmentPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.area_search.user == request.user:
            return True
        return super().has_object_permission(request, view, obj)


class PlotSearchOpeningRecordPermissions(PerMethodPermission):
    def has_permission(self, request, view):
        if PlotSearch.objects.filter(
            preparers__in=User.objects.filter(id=request.user.id)
        ).exists():
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if obj.preparers.filter(id=request.user.id).exists():
            return True
        return super().has_object_permission(request, view, obj)
