from django.contrib.gis import admin
from django.utils.translation import ugettext_lazy as _

from leasing.models import Contact, Decision, Invoice, Tenant
from leasing.models.building_footprint import LeaseBuildingFootprint
from leasing.models.lease import (
    LeaseAdditionalField, LeaseCondition, LeaseIdentifier, LeaseRealPropertyUnit, LeaseRealPropertyUnitAddress)

from .models import Application, ApplicationBuildingFootprint, Area, Lease, Note, Rent


class AreaAdmin(admin.OSMGeoAdmin):
    list_display = ('name', )
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Area, AreaAdmin)


class ApplicationBuildingFootprintInline(admin.TabularInline):
    model = ApplicationBuildingFootprint
    extra = 3


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('contact_name', 'organization_name', 'type', 'state')
    inlines = [ApplicationBuildingFootprintInline]
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Application, ApplicationAdmin)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization_name')
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Contact, ContactAdmin)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('period_start_date', 'period_end_date', 'due_date', 'amount')
    readonly_fields = ('reference_number', 'created_at', 'modified_at')


admin.site.register(Invoice, InvoiceAdmin)


class RentInline(admin.StackedInline):
    model = Rent
    extra = 0


class DecisionInline(admin.StackedInline):
    model = Decision
    extra = 0


class TenantInline(admin.TabularInline):
    model = Tenant
    extra = 0


class LeaseBuildingFootprintInline(admin.TabularInline):
    model = LeaseBuildingFootprint
    extra = 0


class LeaseAdditionalFieldInline(admin.TabularInline):
    model = LeaseAdditionalField
    extra = 0


class LeaseConditionInline(admin.TabularInline):
    model = LeaseCondition
    extra = 0


class LeaseAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'is_reservation', 'is_billing_enabled', 'state')
    inlines = [RentInline, TenantInline, DecisionInline, LeaseBuildingFootprintInline, LeaseAdditionalFieldInline,
               LeaseConditionInline]

    fieldsets = (
        (None, {
            'fields': ('application', 'identifier', 'identifier_type', 'identifier_municipality', 'identifier_district',
                       'state', 'is_reservation', 'reasons', 'start_date', 'end_date', 'bills_per_year',
                       'is_billing_enabled', 'notes', 'areas')
        }),
        (_('Detailed plan'), {
            'fields': ('detailed_plan', 'detailed_plan_area'),
        }),
        (_('Internal details'), {
            'fields': ('preparer', 'created_at', 'modified_at'),
        }),
    )

    readonly_fields = ('identifier', 'created_at', 'modified_at')


admin.site.register(Lease, LeaseAdmin)


class LeaseIdentifierAdmin(admin.ModelAdmin):
    list_display = ('type', 'municipality', 'district', 'sequence')


admin.site.register(LeaseIdentifier, LeaseIdentifierAdmin)


class LeaseRealPropertyUnitAddressInline(admin.TabularInline):
    model = LeaseRealPropertyUnitAddress
    extra = 0


class LeaseRealPropertyUnitAdmin(admin.ModelAdmin):
    model = LeaseRealPropertyUnit
    inlines = [LeaseRealPropertyUnitAddressInline]


admin.site.register(LeaseRealPropertyUnit, LeaseRealPropertyUnitAdmin)


class NoteAdmin(admin.ModelAdmin):
    model = Note
    list_display = ('title',)
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Note, NoteAdmin)


class RentAdmin(admin.ModelAdmin):
    model = Rent
    readonly_fields = ('created_at', 'modified_at')


admin.site.register(Rent, RentAdmin)
