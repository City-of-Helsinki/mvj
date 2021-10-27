from django.contrib import admin

from credit_integration.models import (
    CreditDecision,
    CreditDecisionLog,
    CreditDecisionReason,
)
from field_permissions.admin import FieldPermissionsAdminMixin


@admin.register(CreditDecision)
class CreditDecisionAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):

    raw_id_fields = (
        "customer",
        "claimant",
    )


@admin.register(CreditDecisionReason)
class CreditDecisionReasonAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    pass


@admin.register(CreditDecisionLog)
class CreditDecisionLogAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "identification", "text", "user")
    raw_id_fields = ("user",)
