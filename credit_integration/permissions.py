from rest_framework import permissions

from credit_integration.models import (
    CreditDecision,
    CreditDecisionLog,
    CreditDecisionReason,
)
from utils.enums import AuthGroupId as AG
from utils.group_permissions import GroupModelPermissions

CREDIT_INTEGRATION_GROUP_MODEL_PERMISSIONS: GroupModelPermissions = {
    CreditDecision: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            AG.SOPIMUSVALMISTELIJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            AG.SYOTTAJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            AG.PERINTALAKIMIES: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            AG.LASKUTTAJA: (
                "view",
                "send_creditdecision_inquiry",
                "send_sanctions_inquiry",
            ),
            AG.PAAKAYTTAJA: (
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
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
        },
        "fields": {},
    },
    CreditDecisionLog: {
        "model": {
            AG.SELAILIJA: None,
            AG.VALMISTELIJA: ("view",),
            AG.SOPIMUSVALMISTELIJA: ("view",),
            AG.SYOTTAJA: ("view",),
            AG.PERINTALAKIMIES: ("view",),
            AG.LASKUTTAJA: ("view",),
            AG.PAAKAYTTAJA: ("view", "add", "change", "delete"),
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
