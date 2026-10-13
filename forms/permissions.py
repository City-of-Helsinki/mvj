from forms.models.form import Answer, Attachment, Form
from leasing.permissions import MvjDjangoModelPermissions, PerMethodPermission
from plotsearch.models import PlotSearch
from users.models import User
from utils.group_permissions import UG, GroupModelPermissions

FORMS_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    Form: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Answer: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    Attachment: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}


class AnswerPermissions(PerMethodPermission):
    def has_permission(self, request, view):
        if PlotSearch.objects.filter(
            preparers__in=User.objects.filter(id=request.user.id)
        ).exists():
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if (
            not hasattr(obj, "opening_record")
            and obj.statuses.filter(
                plot_search_target__plot_search__subtype__require_opening_record=True
            ).exists()
        ):
            return False
        if obj.statuses.filter(
            plot_search_target__plot_search__preparers__in=User.objects.filter(
                id=request.user.id
            )
        ).exists():
            return True
        return super().has_object_permission(request, view, obj)


class OpeningRecordPermissions(PerMethodPermission):
    def has_permission(self, request, view):
        if PlotSearch.objects.filter(
            preparers__in=User.objects.filter(id=request.user.id)
        ).exists():
            return True
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if obj.answer.statuses.filter(
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
