from rest_framework import permissions


class SendCreditDecisionInquiryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.send_creditdecision_inquiry")


class CreditDecisionViewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.view_creditdecision")


class SendSanctionsInquiryPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("credit_integration.send_sanctions_inquiry")
