from itertools import groupby

from django.contrib.gis import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from enumfields.admin import EnumFieldListFilter

from field_permissions.admin import FieldPermissionsAdminMixin
from laske_export.exporter import LaskeExporter
from leasing.models import (
    Area,
    AreaNote,
    AreaSource,
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
from leasing.models.lease import ReservationProcedure
from leasing.models.map_layers import VipunenMapLayer
from leasing.models.service_unit import ServiceUnitGroupMapping


class CenterOnHelsinkiGISAdmin(admin.GISModelAdmin):
    # Position 24.945, 60.192 (SRID 4326) transformed to SRID 900913
    default_lon = 2776864.697838209
    default_lat = 8442609.191245062
    default_zoom = 11


@admin.register(AreaNote)
class AreaNoteAdmin(FieldPermissionsAdminMixin, CenterOnHelsinkiGISAdmin):
    list_display = ("created_at", "user")
    search_fields = ["note", "user__first_name", "user__last_name", "user__username"]


class FieldPermissionsModelAdmin(FieldPermissionsAdminMixin, admin.ModelAdmin):
    pass


@admin.register(
    BasisOfRentBuildPermissionType,
    BasisOfRentPlotType,
    CollateralType,
    CommentTopic,
    ConditionType,
    ContractType,
    DecisionMaker,
    Financing,
    Hitas,
    Management,
    PlanUnitIntendedUse,
    PlanUnitState,
    PlanUnitType,
    PlotDivisionState,
    Regulation,
    RentIntendedUse,
    ReservationProcedure,
    SpecialProject,
    StatisticalUse,
    SupportiveHousing,
)
class NameAdmin(FieldPermissionsModelAdmin):
    list_display = ("name",)
    search_fields = ["name"]


@admin.register(Area)
class AreaAdmin(CenterOnHelsinkiGISAdmin):
    list_display = ("identifier", "type", "source")
    list_filter = (("type", EnumFieldListFilter), "source")
    search_fields = ["identifier"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("source")


@admin.register(AreaSource)
class AreaSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier")
    search_fields = ["name", "identifier"]


@admin.register(Contact)
class ContactAdmin(FieldPermissionsModelAdmin):
    list_display = ("__str__", "type", "service_unit", "is_lessor")
    list_filter = (("type", EnumFieldListFilter), "service_unit", "is_lessor")
    search_fields = ["first_name", "last_name", "name"]


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier")
    search_fields = ["name", "identifier"]
    readonly_fields = ("id",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "municipality", "identifier")
    search_fields = ["name", "municipality__name", "identifier"]


@admin.register(TenantContact)
class TenantContactAdmin(FieldPermissionsModelAdmin):
    list_display = ("get_lease_identifier", "tenant", "type", "contact")
    search_fields = ["tenant__lease__identifier__identifier", "contact__name"]
    raw_id_fields = ("tenant", "contact")

    @admin.display(description=_("Lease"))
    def get_lease_identifier(self, obj):
        return str(obj.tenant.lease)

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


@admin.register(Tenant)
class TenantAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "get_tenant_names")
    search_fields = [
        "lease__identifier__identifier",
    ]
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
        ).prefetch_related("contacts")

    @admin.display(description=_("Tenant names"))
    def get_tenant_names(self, obj: Tenant):
        tenant_names: list[str] = [contact.get_name() for contact in obj.contacts.all()]
        return " / ".join(tenant_names) or "-"


class RelatedLeaseInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = RelatedLease
    fk_name = "from_lease"
    raw_id_fields = ("from_lease", "to_lease")
    extra = 0


class LeaseBasisOfRentInline(FieldPermissionsAdminMixin, admin.TabularInline):
    model = LeaseBasisOfRent
    extra = 0


@admin.register(LeaseIdentifier)
class LeaseIdentifierAdmin(FieldPermissionsModelAdmin):
    search_fields = ["identifier"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("type", "municipality", "district")


@admin.register(Lease)
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


@admin.register(CollectionCourtDecision)
class CollectionCourtDecisionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "file", "uploaded_at", "uploader")
    raw_id_fields = ("lease",)
    ordering = ("-uploaded_at",)


@admin.register(CollectionLetter)
class CollectionLetterAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "file", "uploaded_at", "uploader")
    raw_id_fields = ("lease",)
    ordering = ("-uploaded_at",)


@admin.register(CollectionNote)
class CollectionNoteAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "created_at", "note", "user")
    search_fields = [
        "lease__identifier__identifier",
        "user__first_name",
        "user__last_name",
    ]
    list_filter = ("collection_stage",)
    raw_id_fields = ("lease",)
    ordering = ("-created_at",)


@admin.register(CollectionLetterTemplate)
class CollectionLetterTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "modified_at")
    ordering = ("name",)


@admin.register(Comment)
class CommentAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "topic", "user", "created_at", "modified_at")
    raw_id_fields = ("lease",)


class ContractChangeInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = ContractChange
    extra = 0


class CollateralInline(FieldPermissionsAdminMixin, admin.StackedInline):
    model = Collateral
    extra = 0


@admin.register(Contract)
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


@admin.register(Decision)
class DecisionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "reference_number", "decision_maker", "type")
    search_fields = [
        "reference_number",
        "decision_maker__name",
        "lease__identifier__identifier",
    ]
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


@admin.register(DecisionType)
class DecisionTypeAdmin(NameAdmin):
    list_display = ("name", "kind")


@admin.register(Inspection)
class InspectionAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "inspector", "supervision_date", "supervised_date")
    search_fields = ["lease__identifier__identifier", "inspector"]
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


@admin.register(LeaseType)
class LeaseTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "identifier", "id", "is_active")
    list_filter = ("is_active",)
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


@admin.register(Rent)
class RentAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "type")
    search_fields = ["lease__identifier__identifier"]
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


@admin.register(BasisOfRent)
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


@admin.register(Index)
class IndexAdmin(admin.ModelAdmin):
    list_display = ("year", "month", "number")


@admin.register(InfillDevelopmentCompensation)
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


@admin.register(InfillDevelopmentCompensationLease)
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


@admin.register(InterestRate)
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


@admin.register(Invoice)
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
    readonly_fields = ("service_unit",)

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


@admin.register(InvoiceSet)
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


@admin.register(InvoiceNote)
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


@admin.register(ReceivableType)
class ReceivableTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "service_unit", "is_active")
    list_filter = ("service_unit", "is_active")
    search_fields = [
        "name",
        "service_unit__name",
        "sap_material_code",
        "sap_order_item_number",
        "sap_project_number",
    ]
    ordering = (
        "service_unit",
        "name",
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


@admin.register(LeaseArea)
class LeaseAreaAdmin(FieldPermissionsModelAdmin):
    list_display = ("lease", "identifier", "type")
    search_fields = ["lease__identifier__identifier", "identifier"]
    list_filter = ("type",)
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


@admin.register(Plot)
class PlotAdmin(FieldPermissionsModelAdmin):
    list_display = ("get_lease_area_identifier", "type")
    search_fields = ["lease_area__identifier", "type"]
    list_filter = ("type",)
    raw_id_fields = ("lease_area",)

    def get_lease_area_identifier(self, obj):
        return str(obj.lease_area.identifier)

    get_lease_area_identifier.short_description = _("Lease Area Identifier")


@admin.register(LeaseStateLog)
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


@admin.register(PlanUnit)
class PlanUnitAdmin(FieldPermissionsModelAdmin):
    list_display = ("identifier", "get_lease_identifier", "lease_area")
    list_filter = ("plan_unit_type__name",)
    raw_id_fields = ("lease_area",)
    search_fields = ["identifier"]

    @admin.display(description=_("Lease"))
    def get_lease_identifier(self, obj):
        return str(obj.lease_area.lease)

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        return qs.select_related("lease_area", "lease_area__lease")


@admin.register(Vat)
class VatAdmin(admin.ModelAdmin):
    list_display = ("percent", "start_date", "end_date")


@admin.register(UiData)
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


@admin.register(LeaseholdTransfer)
class LeaseholdTransferAdmin(admin.ModelAdmin):
    inlines = [LeaseholdTransferPartyInline, LeaseholdTransferPropertyInline]
    readonly_fields = ("institution_identifier", "decision_date")


@admin.register(LeaseholdTransferImportLog)
class LeaseholdTransferImportLogAdmin(admin.ModelAdmin):
    list_display = ("file_name", "created_at", "modified_at")
    readonly_fields = ("created_at", "modified_at")
    ordering = ("id",)


class ServiceUnitGroupMappingInline(admin.TabularInline):
    model = ServiceUnitGroupMapping
    extra = 0


@admin.register(ServiceUnit)
class ServiceUnitAdmin(admin.ModelAdmin):
    readonly_fields = ("color_display",)
    list_display = ("name", "created_at", "modified_at", "color_display")
    inlines = [ServiceUnitGroupMappingInline]
    readonly_fields = ("created_at", "modified_at")
    ordering = ("name",)

    @admin.display(description=_("Color"))
    def color_display(self, obj: ServiceUnit):
        """Displays `hex_color` as a square."""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {};"></div>',
            obj.hex_color,
        )


@admin.register(ServiceUnitGroupMapping)
class ServiceUnitGroupMappingAdmin(admin.ModelAdmin):
    pass


@admin.register(IntendedUse)
class IntendedUseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "service_unit",
        "is_active",
    )
    search_fields = ["name"]
    list_filter = (
        "is_active",
        "service_unit",
    )
    ordering = (
        "name",
        "service_unit",
    )


@admin.register(VipunenMapLayer)
class VipunenMapLayerAdmin(FieldPermissionsModelAdmin):
    readonly_fields = ("color_display",)
    list_display = (
        "hierarchical_name",
        "color_display",
        "parent",
        "name_fi",
        "keywords",
    )
    list_filter = ("parent",)
    search_fields = ["name_fi", "name_sv", "name_en", "keywords"]
    autocomplete_fields = ["filter_by_lease_type", "filter_by_intended_use"]

    @admin.display(description="Hierarchical name")
    def hierarchical_name(self, obj: VipunenMapLayer):
        return str(obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request).order_by("parent")
        return qs.select_related("parent")

    @admin.display(description="Color")
    def color_display(self, obj: VipunenMapLayer):
        """Displays `hex_color` as a square."""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {};"></div>',
            obj.hex_color,
        )


admin.site.register(NoticePeriod)
