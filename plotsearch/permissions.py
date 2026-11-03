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
from utils.enums import AuthGroupId as AG
from utils.group_permissions import GroupModelPermissions

PLOTSEARCH_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    AreaSearchIntendedUse: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearch: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    PlotSearchStage: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearchType: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    PlotSearchSubtype: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    TargetStatus: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AreaSearch: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {
            "_default": {
                AG.SELAILIJA: None,
                AG.VALMISTELIJA: "change",
                AG.SOPIMUSVALMISTELIJA: "view",
                AG.SYOTTAJA: "change",
                AG.PERINTALAKIMIES: "change",
                AG.LASKUTTAJA: "view",
                AG.PAAKAYTTAJA: "change",
            },
        },
    },
    InformationCheck: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    RelatedPlotApplication: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    AreaSearchAttachment: {
        "model": {
            AG.SELAILIJA: ("view",),
            AG.VALMISTELIJA: ("view", "add"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add"),
            AG.PERINTALAKIMIES: ("view", "add"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add"),
        },
        "fields": {},
    },
    MeetingMemo: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view", "add", "change", "delete"),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view", "add", "change", "delete"),
            AG.PERINTALAKIMIES: ("view", "add", "change", "delete"),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
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
