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
from utils.group_permissions import UG, GroupModelPermissions

PLOTSEARCH_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    AreaSearchIntendedUse: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearch: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    PlotSearchStage: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearchType: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearchSubtype: {
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
    TargetStatus: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AreaSearch: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                UG.SELAILIJA: None,
                UG.VALMISTELIJA: "change",
                UG.SOPIMUSVALMISTELIJA: "view",
                UG.SYOTTAJA: "change",
                UG.PERINTALAKIMIES: "change",
                UG.LASKUTTAJA: "view",
                UG.PAAKAYTTAJA: "change",
            },
        },
    },
    InformationCheck: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add", "change", "delete"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    RelatedPlotApplication: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add", "change", "delete"),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AreaSearchAttachment: {
        "model": {
            UG.SELAILIJA: ("view",),
            UG.VALMISTELIJA: ("view", "add"),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view", "add"),
            UG.PERINTALAKIMIES: ("view", "add"),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add"),
        },
        "fields": {},
    },
    MeetingMemo: {
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
