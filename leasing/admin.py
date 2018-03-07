from django.contrib.gis import admin

from leasing.models import (
    Contact, District, Financing, Hitas, IntendedUse, Lease, LeaseArea, LeaseIdentifier, LeaseStateLog, LeaseType,
    Management, Municipality, NoticePeriod, PlanUnit, PlanUnitState, PlanUnitType, Plot, Regulation, RelatedLease,
    StatisticalUse, SupportiveHousing, Tenant, TenantContact)


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    readonly_fields = ('id',)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'municipality', 'identifier')


class TenantContactInline(admin.TabularInline):
    model = TenantContact
    extra = 0


class TenantAdmin(admin.ModelAdmin):
    list_display = ('lease', )
    inlines = [TenantContactInline]


class LeaseAdmin(admin.ModelAdmin):
    pass


admin.site.register(Contact)
admin.site.register(District, DistrictAdmin)
admin.site.register(Financing)
admin.site.register(Hitas)
admin.site.register(IntendedUse)
admin.site.register(Lease, LeaseAdmin)
admin.site.register(LeaseArea)
admin.site.register(LeaseIdentifier)
admin.site.register(LeaseStateLog)
admin.site.register(LeaseType)
admin.site.register(Management)
admin.site.register(Municipality, MunicipalityAdmin)
admin.site.register(NoticePeriod)
admin.site.register(Plot)
admin.site.register(PlanUnit)
admin.site.register(PlanUnitState)
admin.site.register(PlanUnitType)
admin.site.register(Regulation)
admin.site.register(RelatedLease)
admin.site.register(StatisticalUse)
admin.site.register(SupportiveHousing)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantContact)
