from rest_framework.permissions import IsAuthenticated


class TargetStatusPermissions(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.user.groups.filter(name__icontains="pääkäyttäjä").exists():
            return True
        if not obj.plot_search_target.plot_search.preparers.filter(
            id=request.user.id
        ).exists():
            return False
        return super().has_object_permission(request, view, obj)
