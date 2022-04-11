from itertools import groupby

from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from field_permissions.admin import FieldPermissionsAdminMixin
from laske_export.exporter import LaskeExporter
from leasing.models import (
    Area,
    AreaNote,
    AreaSource,
    BankHoliday,
    BasisOfRent,
    BasisOfRentBuildPermissionType,
    BasisOfRentDecision,
    BasisOfRentPlotType,
    BasisOfRentPropertyIdentifier,
    BasisOfRentRate,
    Collateral,
    CollateralType,
    CollectionCourtDecision,
    CollectionLetter,
    CollectionLetterTemplate,
    CollectionNote,
    Comment,
    CommentTopic,
    Condition,
    ConditionType,
    ConstructabilityDescription,
    Contact,
    Contract,
    ContractChange,
    ContractRent,
    ContractType,
    Decision,
    DecisionMaker,
    DecisionType,
    District,
    Financing,
    FixedInitialYearRent,
    Hitas,
    Index,
    Inspection,
    IntendedUse,
    InterestRate,
    Invoice,
    Lease,
    LeaseArea,
    LeaseBasisOfRent,
    LeaseholdTransfer,
    LeaseholdTransferImportLog,
    LeaseholdTransferParty,
    LeaseholdTransferProperty,
    LeaseIdentifier,
    LeaseStateLog,
    LeaseType,
    Management,
    Municipality,
    NoticePeriod,
    PlanUnit,
    PlanUnitState,
    PlanUnitType,
    Plot,
    ReceivableType,
    Regulation,
    RelatedLease,
    Rent,
    RentAdjustment,
    RentDueDate,
    RentIntendedUse,
    ServiceUnit,
    SpecialProject,
    StatisticalUse,
    SupportiveHousing,
    Tenant,
    TenantContact,
    UiData,
    Vat,
)
from leasing.models.infill_development_compensation import (
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationAttachment,
    InfillDevelopmentCompensationDecision,
    InfillDevelopmentCompensationIntendedUse,
    InfillDevelopmentCompensationLease,
)
from leasing.models.invoice import InvoiceNote, InvoicePayment, InvoiceRow, InvoiceSet
from leasing.models.land_area import (
    LeaseAreaAddress,
    PlanUnitIntendedUse,
    PlotDivisionState,
)
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementConditionFormOfManagement,
    LandUseAgreementDecision,
    LandUseAgreementDecisionCondition,
    LandUseAgreementDecisionConditionType,
    LandUseAgreementDecisionType,
    LandUseAgreementDefinition,
    LandUseAgreementStatus,
    LandUseAgreementType,
)
from leasing.models.lease import ReservationProcedure


class CenterOnHelsinkiOSMGeoAdmin(admin.OSMGeoAdmin):
    # Position 24.945, 60.192 (SRID 4326) transformed to SRID 900913
    default_lon = 2776864.697838209
    default_lat = 8442609.191245062
    default_zoom = 11


class AreaNoteAdmin(FieldPermissionsAdminMixin, CenterOnHelsinkiOSMGeoAdmin):
    pass


class FieldPermissionsModelAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    pass


class NameAdmin(FieldPermissionsModelAdmin):
    list_display = ("name",)
    search_fields = ["name"]


class AreaAdmin(CenterOnHelsinkiOSMGeoAdmin):
    list_display = ("identifier", "type", "source")
    list_filter = (("type", EnumFieldListFilter), "source")
    search_fields = ["identifier"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("source")


class AreaSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier")
    search_fields = ["name", "identifier"]


class ContactAdmin(FieldPermissionsModelAdmin):
    list_display = ("__str__", "type", "service_unit", "is_lessor")
    list_filter = (("type", EnumFieldListFilter), "service_unit", "is_lessor")
    search_fields = ["first_name", "last_name", "name"]


class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier")
    search_fields = ["name", "identifier"]
    readonly_fields = ("id",)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "municipality", "identifier")
    search_fields = ["name", "municipality__name", "identifier"]


class TenantContactAdmin(FieldPermissionsModelAdmin):
    list_display = ("get_lease_identifier", "tenant", "type", "contact")
    raw_id_fields = ("tenant", "contact")

    def get_lease_identifier(self, obj):
        return str(obj.tenant.lease)

    get_lease_identifier.short_description = _("Lease")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "tenant",
            "contact",
            "tenant__lease__type",
            "tenant__lease__municipality",
            "tenant__lease__district",
            "tenant__lease__identifier",
            "tenant__lease__identifier__type",
            "tenant__lease__identifier__municipality",
            "tenant__lease__identifier__district",
        )


class TenantContactInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = TenantContact
    extra = 0


class TenantAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease",)
    inlines = [TenantContactInline]
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class RelatedLeaseInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = RelatedLease
    fk_name = "from_lease"
    raw_id_fields = ("from_lease", "to_lease")
    extra = 0


class LeaseBasisOfRentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = LeaseBasisOfRent
    extra = 0


class LeaseIdentifierAdmin(FieldPermissionsModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("type", "municipality", "district")


class LeaseAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    inlines = [RelatedLeaseInline, LeaseBasisOfRentInline]
    raw_id_fields = ("identifier",)
    search_fields = ("identifier_id__identifier",)
    search_help_text = _("Search by identifier")  # Will be added in django 4.0
    autocomplete_fields = ("lessor",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "type",
            "municipality",
            "district",
            "identifier",
            "identifier__type",
            "identifier__municipality",
            "identifier__district",
        )


class CollectionCourtDecisionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "file", "uploaded_at", "uploader")
    raw_id_fields = ("lease",)
    ordering = ("-uploaded_at",)


class CollectionLetterAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "file", "uploaded_at", "uploader")
    raw_id_fields = ("lease",)
    ordering = ("-uploaded_at",)


class CollectionNoteAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "created_at", "note", "user")
    raw_id_fields = ("lease",)
    ordering = ("-created_at",)


class CollectionLetterTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "modified_at")
    ordering = ("name",)


class CommentAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "topic", "user", "created_at", "modified_at")
    raw_id_fields = ("lease",)


class ContractChangeInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = ContractChange
    extra = 0


class CollateralInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = Collateral
    extra = 0


class ContractAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "type", "contract_number")
    inlines = [ContractChangeInline, CollateralInline]
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "type",
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class ConditionInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = Condition
    extra = 0


class DecisionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "reference_number", "decision_maker", "type")
    inlines = [ConditionInline]
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "decision_maker",
            "type",
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class DecisionTypeAdmin(NameAdmin):
    list_display = ("name", "kind")


class InspectionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "inspector", "supervision_date", "supervised_date")
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class LeaseTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier", "id")
    search_fields = ["name", "identifier", "id"]
    ordering = ("identifier",)


class RentDueDateInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = RentDueDate
    extra = 0


class FixedInitialYearRentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = FixedInitialYearRent
    extra = 0


class ContractRentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = ContractRent
    extra = 0


class RentAdjustmentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = RentAdjustment
    extra = 0


class RentAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "type")
    inlines = [
        RentDueDateInline,
        FixedInitialYearRentInline,
        ContractRentInline,
        RentAdjustmentInline,
    ]
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class BasisOfRentPropertyIdentifierInline(
    FieldPermissionsAdminMixin, admin.TabularInline
):
    model = BasisOfRentPropertyIdentifier
    extra = 0


class BasisOfRentDecisionInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = BasisOfRentDecision
    extra = 0


class BasisOfRentRateInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = BasisOfRentRate
    extra = 0


class BasisOfRentAdmin(FieldPermissionsModelAdmin):
    list_display = ("id", "plot_type", "management", "financing")
    inlines = [
        BasisOfRentPropertyIdentifierInline,
        BasisOfRentDecisionInline,
        BasisOfRentRateInline,
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "plot_type", "management", "financing", "index"
        ).prefetch_related(
            "rent_rates",
            "property_identifiers",
            "decisions",
            "decisions__decision_maker",
        )


class IndexAdmin(admin.ModelAdmin):
    list_display = ("year", "month", "number")


class InfillDevelopmentCompensationAdmin(FieldPermissionsModelAdmin):
    list_display = ("name", "reference_number", "state")


class InfillDevelopmentCompensationDecisionInline(
    FieldPermissionsAdminMixin, admin.StackedInline
):
    model = InfillDevelopmentCompensationDecision
    extra = 0


class InfillDevelopmentCompensationIntendedUseInline(
    FieldPermissionsAdminMixin, admin.StackedInline
):
    model = InfillDevelopmentCompensationIntendedUse
    extra = 0


class InfillDevelopmentCompensationAttachmentInline(
    FieldPermissionsAdminMixin, admin.StackedInline
):
    model = InfillDevelopmentCompensationAttachment
    extra = 0


class InfillDevelopmentCompensationLeaseAdmin(FieldPermissionsModelAdmin):
    raw_id_fields = ("lease",)
    inlines = [
        InfillDevelopmentCompensationDecisionInline,
        InfillDevelopmentCompensationIntendedUseInline,
        InfillDevelopmentCompensationAttachmentInline,
    ]
    list_display = ("infill_development_compensation", "lease")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class InterestRateAdmin(admin.ModelAdmin):
    list_display = ("start_date", "end_date", "reference_rate", "penalty_rate")
    ordering = ("-start_date", "-end_date")


class InvoicePaymentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = InvoicePayment
    extra = 0


class InvoiceRowInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = InvoiceRow
    extra = 0
    raw_id_fields = ("tenant",)


class InvoiceAdmin(FieldPermissionsModelAdmin):
    actions = ["resend_invoice"]

    def resend_invoice(self, request, queryset):
        invoice_count = 0
        for service_unit, group in groupby(queryset, lambda i: i.service_unit):
            invoices = list(group)
            invoice_count += len(invoices)

            exporter = LaskeExporter(service_unit=service_unit)
            exporter.export_invoices(invoices)

        self.message_user(request, f"Invoice resent for {invoice_count} invoices.")

    list_display = (
        "number",
        "lease",
        "due_date",
        "billing_period_start_date",
        "billing_period_end_date",
        "total_amount",
        "sent_to_sap_at",
    )
    search_fields = ("number", "lease__identifier__identifier")
    inlines = [InvoiceRowInline, InvoicePaymentInline]
    raw_id_fields = ("lease", "invoiceset", "credited_invoice", "interest_invoice_for")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class InvoiceSetAdmin(admin.ModelAdmin):
    list_display = ("lease", "billing_period_start_date", "billing_period_end_date")
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class InvoiceNoteAdmin(admin.ModelAdmin):
    list_display = (
        "lease",
        "billing_period_start_date",
        "billing_period_end_date",
        "notes",
    )
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class ConstructabilityDescriptionInline(
    FieldPermissionsAdminMixin, admin.TabularInline
):
    model = ConstructabilityDescription
    extra = 0


class PlotInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = Plot
    extra = 0


class PlanUnitInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = PlanUnit
    extra = 0


class LeaseAreaAddressInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = LeaseAreaAddress
    extra = 0


class LeaseAreaAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "type")
    inlines = [
        LeaseAreaAddressInline,
        ConstructabilityDescriptionInline,
        PlotInline,
        PlanUnitInline,
    ]
    raw_id_fields = ("lease",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class PlotAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease_area", "type")
    raw_id_fields = ("lease_area",)


class LeaseStateLogAdmin(admin.ModelAdmin):
    list_display = ("lease", "state")
    raw_id_fields = ("lease",)
    readonly_fields = ("created_at", "modified_at")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related(
            "lease__type",
            "lease__municipality",
            "lease__district",
            "lease__identifier",
            "lease__identifier__type",
            "lease__identifier__municipality",
            "lease__identifier__district",
        )


class PlanUnitAdmin(FieldPermissionsModelAdmin):
    list_display = ("get_lease_identifier", "lease_area")
    raw_id_fields = ("lease_area",)

    def get_lease_identifier(self, obj):
        return str(obj.lease_area.lease)

    get_lease_identifier.short_description = _("Lease")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("lease_area", "lease_area__lease")


class VatAdmin(admin.ModelAdmin):
    list_display = ("percent", "start_date", "end_date")


class UiDataAdmin(admin.ModelAdmin):
    list_display = ("user", "key")
    list_filter = ("user", "key")
    ordering = ("-user",)


class ReadOnlyTabularInline(admin.TabularInline):
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class LeaseholdTransferPartyInline(ReadOnlyTabularInline):
    model = LeaseholdTransferParty


class LeaseholdTransferPropertyInline(ReadOnlyTabularInline):
    model = LeaseholdTransferProperty


class LeaseholdTransferAdmin(admin.ModelAdmin):
    inlines = [LeaseholdTransferPartyInline, LeaseholdTransferPropertyInline]
    readonly_fields = ("institution_identifier", "decision_date")


class LeaseholdTransferImportLogAdmin(admin.ModelAdmin):
    list_display = ("file_name", "created_at", "modified_at")
    readonly_fields = ("created_at", "modified_at")
    ordering = ("id",)


class LandUseAgreementAddressInline(admin.TabularInline):
    model = LandUseAgreementAddress
    extra = 0


class LandUseAgreementDecisionConditionInline(
    FieldPermissionsAdminMixin, admin.StackedInline
):
    model = LandUseAgreementDecisionCondition
    extra = 0


class LandUseAgreementDecisionAdmin(admin.ModelAdmin):
    inlines = [LandUseAgreementDecisionConditionInline]


class LandUseAgreementAdmin(admin.ModelAdmin):
    inlines = [LandUseAgreementAddressInline]


class ServiceUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "modified_at")
    readonly_fields = ("created_at", "modified_at")
    ordering = ("name",)


admin.site.register(Area, AreaAdmin)
admin.site.register(AreaSource, AreaSourceAdmin)
admin.site.register(AreaNote, AreaNoteAdmin)
admin.site.register(BankHoliday)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentTopic, NameAdmin)
admin.site.register(CollateralType, NameAdmin)
admin.site.register(CollectionCourtDecision, CollectionCourtDecisionAdmin)
admin.site.register(CollectionLetter, CollectionLetterAdmin)
admin.site.register(CollectionLetterTemplate, CollectionLetterTemplateAdmin)
admin.site.register(CollectionNote, CollectionNoteAdmin)
admin.site.register(District, DistrictAdmin)
admin.site.register(Financing, NameAdmin)
admin.site.register(Hitas, NameAdmin)
admin.site.register(Index, IndexAdmin)
admin.site.register(InfillDevelopmentCompensation, InfillDevelopmentCompensationAdmin)
admin.site.register(
    InfillDevelopmentCompensationLease, InfillDevelopmentCompensationLeaseAdmin
)
admin.site.register(IntendedUse, NameAdmin)
admin.site.register(InterestRate, InterestRateAdmin)
admin.site.register(Inspection, InspectionAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceNote, InvoiceNoteAdmin)
admin.site.register(InvoiceSet, InvoiceSetAdmin)
admin.site.register(Lease, LeaseAdmin)
admin.site.register(LeaseArea, LeaseAreaAdmin)
admin.site.register(LeaseIdentifier, LeaseIdentifierAdmin)
admin.site.register(LeaseStateLog, LeaseStateLogAdmin)
admin.site.register(LeaseType, LeaseTypeAdmin)
admin.site.register(LeaseholdTransfer, LeaseholdTransferAdmin)
admin.site.register(LeaseholdTransferImportLog, LeaseholdTransferImportLogAdmin)
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
admin.site.register(ReservationProcedure, NameAdmin)
admin.site.register(ServiceUnit, ServiceUnitAdmin)
admin.site.register(SpecialProject, NameAdmin)
admin.site.register(StatisticalUse, NameAdmin)
admin.site.register(SupportiveHousing, NameAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(TenantContact, TenantContactAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(ContractType, NameAdmin)
admin.site.register(Decision, DecisionAdmin)
admin.site.register(DecisionType, DecisionTypeAdmin)
admin.site.register(DecisionMaker, NameAdmin)
admin.site.register(ConditionType, NameAdmin)
admin.site.register(BasisOfRent, BasisOfRentAdmin)
admin.site.register(BasisOfRentPlotType, NameAdmin)
admin.site.register(BasisOfRentBuildPermissionType, NameAdmin)
admin.site.register(UiData, UiDataAdmin)
admin.site.register(Vat, VatAdmin)

admin.site.register(LandUseAgreementType, NameAdmin)
admin.site.register(LandUseAgreementStatus, NameAdmin)
admin.site.register(LandUseAgreementDefinition, NameAdmin)
admin.site.register(LandUseAgreementDecisionType, NameAdmin)
admin.site.register(LandUseAgreementConditionFormOfManagement, NameAdmin)
admin.site.register(LandUseAgreementDecisionConditionType, NameAdmin)
admin.site.register(LandUseAgreementDecision, LandUseAgreementDecisionAdmin)
admin.site.register(LandUseAgreement, LandUseAgreementAdmin)
