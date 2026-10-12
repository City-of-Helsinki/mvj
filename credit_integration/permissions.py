from rest_framework import permissions

from credit_integration.models import (
    CreditDecision,
    CreditDecisionLog,
    CreditDecisionReason,
)
from utils.group_permissions import UG, GroupModelPermissions

CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    CreditDecision: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            UG.SOPIMUSVALMISTELIJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            UG.SYOTTAJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            UG.PERINTALAKIMIES: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            UG.LASKUTTAJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            UG.PAAKAYTTAJA: (
                "view",
                "add",
                "change",
                "delete",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
        },
        "fields": {},
    },
    CreditDecisionReason: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    CreditDecisionLog: {
        "model": {
            UG.SELAILIJA: None,
            UG.VALMISTELIJA: ("view",),
            UG.SOPIMUSVALMISTELIJA: ("view",),
            UG.SYOTTAJA: ("view",),
            UG.PERINTALAKIMIES: ("view",),
            UG.LASKUTTAJA: ("view",),
            UG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
}


class SendCreditDecisionInquiryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.send_creditdecision_inquiry")


class CreditDecisionViewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.view_creditdecision")


class SendSanctionsInquiryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.send_sanctions_inquiry")
