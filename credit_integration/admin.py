from django.contrib import admin

from credit_integration.models import CreditDecision, CreditDecisionReason
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
