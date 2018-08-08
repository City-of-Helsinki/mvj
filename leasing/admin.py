from django.contrib.gis import admin
from django.utils.translation import ugettext_lazy as _

from leasing.models import (
    AreaNote, BankHoliday, BasisOfRent, BasisOfRentBuildPermissionType, BasisOfRentDecision, BasisOfRentPlotType,
    BasisOfRentPropertyIdentifier, BasisOfRentRate, Comment, CommentTopic, Condition, ConditionType,
    ConstructabilityDescription, Contact, Contract, ContractChange, ContractRent, ContractType, Decision, DecisionMaker,
    DecisionType, District, Financing, FixedInitialYearRent, Hitas, Index, Inspection, IntendedUse, Invoice, Lease,
    LeaseArea, LeaseBasisOfRent, LeaseIdentifier, LeaseStateLog, LeaseType, Management, MortgageDocument, Municipality,
    NoticePeriod, PlanUnit, PlanUnitState, PlanUnitType, Plot, ReceivableType, Regulation, RelatedLease, Rent,
    RentAdjustment, RentDueDate, RentIntendedUse, StatisticalUse, SupportiveHousing, Tenant, TenantContact)
from leasing.models.infill_development_compensation import (
    InfillDevelopmentCompensation, InfillDevelopmentCompensationAttachment, InfillDevelopmentCompensationDecision,
    InfillDevelopmentCompensationIntendedUse, InfillDevelopmentCompensationLease)
from leasing.models.invoice import InvoicePayment, InvoiceRow, InvoiceSet
from leasing.models.land_area import (
    LeaseAreaAddress, PlanUnitAddress, PlanUnitIntendedUse, PlotAddress, PlotDivisionState)


class CenterOnHelsinkiOSMGeoAdmin(admin.OSMGeoAdmin):
    # Position 24.945, 60.192 (SRID 4326) transformed to SRID 900913
    default_lon = 2776864.697838209
    default_lat = 8442609.191245062
    default_zoom = 11


class AreaNoteAdmin(CenterOnHelsinkiOSMGeoAdmin):
    pass


class ContactAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'type', 'is_lessor')
    search_fields = ['first_name', 'last_name', 'name']


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    readonly_fields = ('id',)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'municipality', 'identifier')
    search_fields = ['name', 'municipality__name', 'identifier']


class TenantContactAdmin(admin.ModelAdmin):
    list_display = ('get_lease_identifier', 'tenant', 'type', 'contact')
    raw_id_fields = ('tenant', 'contact')

    def get_lease_identifier(self, obj):
        return str(obj.tenant.lease)

    get_lease_identifier.short_description = _('Lease')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('tenant', 'contact', 'tenant__lease__type', 'tenant__lease__municipality',
                                 'tenant__lease__district', 'tenant__lease__identifier',
                                 'tenant__lease__identifier__type', 'tenant__lease__identifier__municipality',
                                 'tenant__lease__identifier__district')


class TenantContactInline(admin.TabularInline):
    model = TenantContact
    extra = 0


class TenantAdmin(admin.ModelAdmin):
    list_display = ('lease', )
    inlines = [TenantContactInline]
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class RelatedLeaseInline(admin.TabularInline):
    model = RelatedLease
    fk_name = 'from_lease'
    raw_id_fields = ('from_lease', 'to_lease')
    extra = 0


class LeaseBasisOfRentInline(admin.TabularInline):
    model = LeaseBasisOfRent
    extra = 0


class LeaseIdentifierAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('type', 'municipality', 'district')


class LeaseAdmin(admin.ModelAdmin):
    inlines = [RelatedLeaseInline, LeaseBasisOfRentInline]
    raw_id_fields = ('identifier', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('type', 'municipality', 'district', 'identifier',
                                 'identifier__type', 'identifier__municipality',
                                 'identifier__district')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('lease', 'topic', 'user', 'created_at', 'modified_at')
    raw_id_fields = ('lease', )


class ContractChangeInline(admin.StackedInline):
    model = ContractChange
    extra = 0


class MortgageDocumentInline(admin.StackedInline):
    model = MortgageDocument
    extra = 0


class ContractAdmin(admin.ModelAdmin):
    list_display = ('lease', 'type', 'contract_number')
    inlines = [ContractChangeInline, MortgageDocumentInline]
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('type', 'lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class ConditionInline(admin.StackedInline):
    model = Condition
    extra = 0


class DecisionAdmin(admin.ModelAdmin):
    list_display = ('lease', 'reference_number', 'decision_maker', 'type')
    inlines = [ConditionInline]
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('decision_maker', 'type', 'lease__type', 'lease__municipality', 'lease__district',
                                 'lease__identifier', 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class InspectionAdmin(admin.ModelAdmin):
    list_display = ('lease', 'inspector', 'supervision_date', 'supervised_date')
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class NameAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ['name']


class LeaseTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    search_fields = ['id', 'name']
    ordering = ('id',)


class RentDueDateInline(admin.TabularInline):
    model = RentDueDate
    extra = 0


class FixedInitialYearRentInline(admin.TabularInline):
    model = FixedInitialYearRent
    extra = 0


class ContractRentInline(admin.TabularInline):
    model = ContractRent
    extra = 0


class RentAdjustmentInline(admin.TabularInline):
    model = RentAdjustment
    extra = 0


class RentAdmin(admin.ModelAdmin):
    list_display = ('lease', 'type')
    inlines = [RentDueDateInline, FixedInitialYearRentInline, ContractRentInline, RentAdjustmentInline]
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class BasisOfRentPropertyIdentifierInline(admin.TabularInline):
    model = BasisOfRentPropertyIdentifier
    extra = 0


class BasisOfRentDecisionInline(admin.TabularInline):
    model = BasisOfRentDecision
    extra = 0


class BasisOfRentRateInline(admin.TabularInline):
    model = BasisOfRentRate
    extra = 0


class BasisOfRentAdmin(admin.ModelAdmin):
    list_display = ('id', 'plot_type', 'management', 'financing')
    inlines = [BasisOfRentPropertyIdentifierInline, BasisOfRentDecisionInline, BasisOfRentRateInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('plot_type', 'management', 'financing', 'index').prefetch_related(
            'rent_rates', 'property_identifiers', 'decisions', 'decisions__decision_maker')


class IndexAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'number')


class InfillDevelopmentCompensationAdmin(admin.ModelAdmin):
    list_display = ('name', 'reference_number', 'state')


class InfillDevelopmentCompensationDecisionInline(admin.StackedInline):
    model = InfillDevelopmentCompensationDecision
    extra = 0


class InfillDevelopmentCompensationIntendedUseInline(admin.StackedInline):
    model = InfillDevelopmentCompensationIntendedUse
    extra = 0


class InfillDevelopmentCompensationAttachmentInline(admin.StackedInline):
    model = InfillDevelopmentCompensationAttachment
    extra = 0


class InfillDevelopmentCompensationLeaseAdmin(admin.ModelAdmin):
    raw_id_fields = ('lease', )
    inlines = [InfillDevelopmentCompensationDecisionInline, InfillDevelopmentCompensationIntendedUseInline,
               InfillDevelopmentCompensationAttachmentInline]
    list_display = ('infill_development_compensation', 'lease')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment
    extra = 0


class InvoiceRowInline(admin.TabularInline):
    model = InvoiceRow
    extra = 0
    raw_id_fields = ('tenant',)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('lease', 'due_date', 'billing_period_start_date', 'billing_period_end_date', 'total_amount')
    inlines = [InvoiceRowInline, InvoicePaymentInline]
    raw_id_fields = ('lease', 'invoiceset', 'credited_invoice')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class InvoiceSetAdmin(admin.ModelAdmin):
    list_display = ('lease', 'billing_period_start_date', 'billing_period_end_date')
    raw_id_fields = ('lease', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class ConstructabilityDescriptionInline(admin.TabularInline):
    model = ConstructabilityDescription
    extra = 0


class PlotInline(admin.StackedInline):
    model = Plot
    extra = 0


class PlanUnitInline(admin.StackedInline):
    model = PlanUnit
    extra = 0


class LeaseAreaAddressInline(admin.TabularInline):
    model = LeaseAreaAddress
    extra = 0


class LeaseAreaAdmin(admin.ModelAdmin):
    list_display = ('lease', 'type')
    inlines = [LeaseAreaAddressInline, ConstructabilityDescriptionInline, PlotInline, PlanUnitInline]
    raw_id_fields = ('lease',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class PlotAddressInline(admin.TabularInline):
    model = PlotAddress
    extra = 0


class PlotAdmin(admin.ModelAdmin):
    list_display = ('lease_area', 'type')
    inlines = [PlotAddressInline]
    raw_id_fields = ('lease_area',)


class LeaseStateLogAdmin(admin.ModelAdmin):
    list_display = ('lease', 'state')
    raw_id_fields = ('lease',)
    readonly_fields = ('created_at', 'modified_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease__type', 'lease__municipality', 'lease__district', 'lease__identifier',
                                 'lease__identifier__type', 'lease__identifier__municipality',
                                 'lease__identifier__district')


class PlanUnitAddressInline(admin.TabularInline):
    model = PlanUnitAddress
    extra = 0


class PlanUnitAdmin(admin.ModelAdmin):
    list_display = ('get_lease_identifier', 'lease_area', 'type')
    inlines = [PlanUnitAddressInline]
    raw_id_fields = ('lease_area',)

    def get_lease_identifier(self, obj):
        return str(obj.lease_area.lease)

    get_lease_identifier.short_description = _('Lease')

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related('lease_area', 'lease_area__lease')


admin.site.register(AreaNote, AreaNoteAdmin)
admin.site.register(BankHoliday)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentTopic, NameAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Financing, NameAdmin)
admin.site.register(Hitas, NameAdmin)
admin.site.register(Index, IndexAdmin)
admin.site.register(InfillDevelopmentCompensation, InfillDevelopmentCompensationAdmin)
admin.site.register(InfillDevelopmentCompensationLease, InfillDevelopmentCompensationLeaseAdmin)
admin.site.register(IntendedUse, NameAdmin)
admin.site.register(Inspection, InspectionAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceSet, InvoiceSetAdmin)
admin.site.register(Lease, LeaseAdmin)
admin.site.register(LeaseArea, LeaseAreaAdmin)
admin.site.register(LeaseIdentifier, LeaseIdentifierAdmin)
admin.site.register(LeaseStateLog, LeaseStateLogAdmin)
admin.site.register(LeaseType, LeaseTypeAdmin)
admin.site.register(Management, NameAdmin)
admin.site.register(Municipality, MunicipalityAdmin)
admin.site.register(NoticePeriod)
admin.site.register(Plot, PlotAdmin)
admin.site.register(PlanUnit, PlanUnitAdmin)
admin.site.register(PlanUnitState, NameAdmin)
admin.site.register(PlanUnitIntendedUse, NameAdmin)
admin.site.register(PlanUnitType, NameAdmin)
admin.site.register(PlotDivisionState, NameAdmin)
admin.site.register(ReceivableType)
admin.site.register(Regulation, NameAdmin)
admin.site.register(Rent, RentAdmin)
admin.site.register(RentIntendedUse, NameAdmin)
admin.site.register(StatisticalUse, NameAdmin)
admin.site.register(SupportiveHousing, NameAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantContact, TenantContactAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(ContractType, NameAdmin)
admin.site.register(Decision, DecisionAdmin)
admin.site.register(DecisionType, NameAdmin)
admin.site.register(DecisionMaker, NameAdmin)
admin.site.register(ConditionType, NameAdmin)
admin.site.register(BasisOfRent, BasisOfRentAdmin)
admin.site.register(BasisOfRentPlotType, NameAdmin)
admin.site.register(BasisOfRentBuildPermissionType, NameAdmin)
