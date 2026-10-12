from leasing.permissions import PerMethodPermission
from plotsearch.models import PlotSearch
from users.models import User
from utils.group_permissions import UG

PLOTSEARCH_GROUP_MODEL_PERMISSIONS = {
    "areasearchintendeduse": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view",),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view",),
        UG.PERINTALAKIMIES: ("view",),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "plotsearch": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "plotsearchstage": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "plotsearchtype": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "plotsearchsubtype": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "targetstatus": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "areasearch": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "informationcheck": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "relatedplotapplication": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view",),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view",),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    "areasearchattachment": {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add"),
        UG.PERINTALAKIMIES: ("view", "add"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add"),
    },
    "meetingmemo": {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
}


class AreaSearchPublicPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.answer is not None:
            return False
        if obj.user and obj.user != request.user:
            return False
        return super().has_object_permission(request, view, obj)


class AreaSearchAttachmentPublicPermissions(PerMethodPermission):
    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
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
