from leasing.permissions import PerMethodPermission
from plotsearch.models import (
    AreaSearch,
    AreaSearchAttachment,
    AreaSearchIntendedUse,
    InformationCheck,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchType,
    RelatedPlotApplication,
    TargetStatus,
)
from plotsearch.models.plot_search import MeetingMemo
from users.models import User
from utils.group_permissions import UG

PLOTSEARCH_GROUP_MODEL_PERMISSIONS = {
    AreaSearchIntendedUse: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view",),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view",),
        UG.PERINTALAKIMIES: ("view",),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    PlotSearch: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    PlotSearchStage: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    PlotSearchType: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    PlotSearchSubtype: {
        UG.SELAILIJA: None,
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    TargetStatus: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    AreaSearch: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    InformationCheck: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add", "change", "delete"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    RelatedPlotApplication: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view",),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add", "change", "delete"),
        UG.PERINTALAKIMIES: ("view",),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
    },
    AreaSearchAttachment: {
        UG.SELAILIJA: ("view",),
        UG.VALMISTELIJA: ("view", "add"),
        UG.SOPIMUSVALMISTELIJA: ("view",),
        UG.SYOTTAJA: ("view", "add"),
        UG.PERINTALAKIMIES: ("view", "add"),
        UG.LASKUTTAJA: ("view",),
        UG.PAAKAYTTAJA: ("view", "add"),
    },
    MeetingMemo: {
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
