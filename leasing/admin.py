from django.contrib.gis import admin

from leasing.models import (
    Contact, District, Financing, Hitas, IntendedUse, Lease, LeaseArea, LeaseIdentifier, LeaseStateLog, LeaseType,
    Management, Municipality, NoticePeriod, PlanUnit, PlanUnitState, PlanUnitType, Plot, Regulation, RelatedLease,
    StatisticalUse, SupportiveHousing, Tenant, TenantContact)


class ContactAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_business', 'is_lessor')
    search_fields = ['first_name', 'last_name', 'business_name']


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    readonly_fields = ('id',)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'municipality', 'identifier')
    search_fields = ['name', 'municipality__name', 'identifier']


class TenantContactInline(admin.TabularInline):
    model = TenantContact
    extra = 0


class TenantAdmin(admin.ModelAdmin):
    list_display = ('lease', )
    inlines = [TenantContactInline]


class LeaseAdmin(admin.ModelAdmin):
    pass


class NameAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ['name']


admin.site.register(Contact, ContactAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Financing, NameAdmin)
admin.site.register(Hitas, NameAdmin)
admin.site.register(IntendedUse, NameAdmin)
admin.site.register(Lease, LeaseAdmin)
admin.site.register(LeaseArea)
admin.site.register(LeaseIdentifier)
admin.site.register(LeaseStateLog)
admin.site.register(LeaseType, NameAdmin)
admin.site.register(Management, NameAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
admin.site.register(NoticePeriod)
admin.site.register(Plot)
admin.site.register(PlanUnit)
admin.site.register(PlanUnitState, NameAdmin)
admin.site.register(PlanUnitType, NameAdmin)
admin.site.register(Regulation, NameAdmin)
admin.site.register(RelatedLease)
admin.site.register(StatisticalUse, NameAdmin)
admin.site.register(SupportiveHousing, NameAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantContact)
