from rest_framework.authtoken.models import Token as TokenAuthenticationModel
from rest_framework.permissions import BasePermission


class ExportLeaseAreaPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_area")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_area")
        )


class ExportVipunenMapLayerPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_vipunen_map_layer")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_vipunen_map_layer")
        )


class ExportLeaseStatisticReportPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_statistic_report")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_statistic_report")
        )


class ExportExpiredLeasePermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_expired_lease")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_expired_lease")
        )


class ExportLeaseProcessingTimeReportPermission(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_processing_time_report")
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and isinstance(request.auth, TokenAuthenticationModel)
            and request.user.has_perm("leasing.export_api_lease_processing_time_report")
        )
