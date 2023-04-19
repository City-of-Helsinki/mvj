from leasing.permissions import MvjDjangoModelPermissions, PerMethodPermission
from users.models import User


class AnswerPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.statuses.filter(
            plot_search_target__plot_search__preparers__in=User.objects.filter(
                id=request.user.id
            )
        ).exists():
            return True
        return super().has_object_permission(request, view, obj)


class AttachmentPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        return super().has_object_permission(request, view, obj)


class TargetStatusPermissions(MvjDjangoModelPermissions):
    def has_object_permission(self, request, view, obj):
        if obj.plot_search_target.plot_search.preparers.filter(
            id=request.user.id
        ).exists():
            return True
        return super().has_object_permission(request, view, obj)
