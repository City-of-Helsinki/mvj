from django.contrib import admin

from landuse.models.agreement import (
    AgreementAddress,
    AgreementPreparer,
    AuthorizedSignatory,
    DetailedPlan,
    District,
    LandUseAgreement,
)
from landuse.models.compensation import LandPolicyProgram, LandUseCompensation
from landuse.models.contract import (
    CashDepositCollateral,
    Contract,
    ContractChange,
    DepositPledgeCollateral,
    MortgageDeedCollateral,
    MortgageDeedPropertyIdentifier,
    OtherCollateral,
    PersonalGuaranteeCollateral,
)
from landuse.models.decision import Decision, DecisionCondition
from landuse.models.invoice import (
    Invoice,
    InvoiceItem,
    InvoiceRecipientSnapshot,
    ShadowSalesLedgerEntry,
)
from landuse.models.party import (
    AgreementParty,
    BillingDetails,
    ContactPerson,
    InvoiceRecipient,
)
from landuse.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleInstallment,
    PaymentScheduleInstallmentItem,
)
from landuse.models.site import (
    AgreementSite,
    DetailedPlanSite,
    SiteIntendedUse,
    SiteTenureType,
)


class AgreementAddressInline(admin.TabularInline):
    model = AgreementAddress
    extra = 0


class AgreementPreparerInline(admin.TabularInline):
    model = AgreementPreparer
    extra = 0
    raw_id_fields = ("preparer",)


class AgreementPartyInline(admin.TabularInline):
    model = AgreementParty
    extra = 0
    show_change_link = True


class AgreementSiteInline(admin.TabularInline):
    model = AgreementSite
    extra = 0
    show_change_link = True


class DecisionInline(admin.TabularInline):
    model = Decision
    extra = 0
    show_change_link = True


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0
    show_change_link = True


class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 0
    show_change_link = True


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    show_change_link = True
    readonly_fields = ("sent_at",)


@admin.register(LandUseAgreement)
class LandUseAgreementAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "status",
        "agreement_type",
        "district",
        "estimated_presentation_year",
        "estimated_payment_year",
        "modified_at",
    )
    list_filter = ("status", "agreement_type", "district", "is_promotion_area")
    search_fields = ("identifier", "district__name", "detailed_plan__plan_number")
    autocomplete_fields = ("district", "authorized_signatory", "detailed_plan")
    readonly_fields = ("created_at", "modified_at")
    inlines = (
        AgreementAddressInline,
        AgreementPreparerInline,
        AgreementPartyInline,
        AgreementSiteInline,
        DecisionInline,
        ContractInline,
        PaymentScheduleInline,
        InvoiceInline,
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("district", "authorized_signatory", "detailed_plan")
        )


class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0


class BillingDetailsInline(admin.StackedInline):
    model = BillingDetails
    extra = 0
    max_num = 1


class InvoiceRecipientInline(admin.StackedInline):
    model = InvoiceRecipient
    extra = 0
    max_num = 1


@admin.register(AgreementParty)
class AgreementPartyAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "party_type", "business_id", "agreement")
    list_filter = ("role", "party_type", "country")
    search_fields = (
        "name",
        "business_id",
        "national_identification_number",
        "agreement__identifier",
    )
    autocomplete_fields = ("agreement",)
    inlines = (ContactPersonInline, BillingDetailsInline, InvoiceRecipientInline)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("agreement")


@admin.register(AgreementAddress)
class AgreementAddressAdmin(admin.ModelAdmin):
    list_display = ("street_address", "postal_code", "city", "agreement")
    search_fields = ("street_address", "postal_code", "city", "agreement__identifier")
    autocomplete_fields = ("agreement",)


@admin.register(AgreementPreparer)
class AgreementPreparerAdmin(admin.ModelAdmin):
    list_display = ("agreement", "preparer")
    search_fields = (
        "agreement__identifier",
        "preparer__first_name",
        "preparer__last_name",
        "preparer__username",
    )
    autocomplete_fields = ("agreement", "preparer")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("identifier", "name")
    search_fields = ("identifier", "name")
    ordering = ("identifier",)


@admin.register(AuthorizedSignatory)
class AuthorizedSignatoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(DetailedPlan)
class DetailedPlanAdmin(admin.ModelAdmin):
    list_display = (
        "plan_number",
        "processing_stage",
        "approval_date",
        "effective_date",
    )
    list_filter = ("processing_stage",)
    search_fields = ("plan_number", "diary_number", "approver")
    ordering = ("plan_number",)


@admin.register(LandUseCompensation)
class LandUseCompensationAdmin(admin.ModelAdmin):
    list_display = (
        "agreement",
        "total_compensation",
        "land_use_compensation",
        "land_policy_program",
    )
    search_fields = ("agreement__identifier", "land_policy_program__name")
    autocomplete_fields = ("agreement", "land_policy_program")


@admin.register(LandPolicyProgram)
class LandPolicyProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "default_discount_percentage")
    search_fields = ("name",)
    ordering = ("name",)


class ContractChangeInline(admin.StackedInline):
    model = ContractChange
    extra = 0


class MortgageDeedCollateralInline(admin.StackedInline):
    model = MortgageDeedCollateral
    extra = 0
    filter_horizontal = ("parties",)


class CashDepositCollateralInline(admin.StackedInline):
    model = CashDepositCollateral
    extra = 0
    filter_horizontal = ("parties",)


class PersonalGuaranteeCollateralInline(admin.StackedInline):
    model = PersonalGuaranteeCollateral
    extra = 0
    filter_horizontal = ("parties",)


class DepositPledgeCollateralInline(admin.StackedInline):
    model = DepositPledgeCollateral
    extra = 0
    filter_horizontal = ("parties",)


class OtherCollateralInline(admin.StackedInline):
    model = OtherCollateral
    extra = 0
    filter_horizontal = ("parties",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "contract_number",
        "contract_type",
        "agreement",
        "signing_date",
    )
    list_filter = ("contract_type",)
    search_fields = ("title", "contract_number", "agreement__identifier")
    autocomplete_fields = ("agreement", "decision")
    inlines = (
        ContractChangeInline,
        MortgageDeedCollateralInline,
        CashDepositCollateralInline,
        PersonalGuaranteeCollateralInline,
        DepositPledgeCollateralInline,
        OtherCollateralInline,
    )


@admin.register(ContractChange)
class ContractChangeAdmin(admin.ModelAdmin):
    list_display = ("contract", "signing_date", "signing_deadline")
    search_fields = ("contract__contract_number", "contract__agreement__identifier")
    autocomplete_fields = ("contract", "decision")


@admin.register(MortgageDeedCollateral)
class MortgageDeedCollateralAdmin(admin.ModelAdmin):
    list_display = ("mortgage_deed_number", "contract", "amount", "returned_date")
    search_fields = ("mortgage_deed_number", "contract__contract_number")
    autocomplete_fields = ("contract",)
    filter_horizontal = ("parties",)


@admin.register(CashDepositCollateral)
class CashDepositCollateralAdmin(admin.ModelAdmin):
    list_display = (
        "account_number",
        "contract",
        "amount",
        "paid_at_date",
        "returned_date",
    )
    search_fields = ("account_number", "contract__contract_number")
    autocomplete_fields = ("contract",)
    filter_horizontal = ("parties",)


@admin.register(PersonalGuaranteeCollateral)
class PersonalGuaranteeCollateralAdmin(admin.ModelAdmin):
    list_display = ("guarantee_identifier", "guarantor_name", "contract", "amount")
    search_fields = (
        "guarantee_identifier",
        "guarantor_name",
        "contract__contract_number",
    )
    autocomplete_fields = ("contract",)
    filter_horizontal = ("parties",)


@admin.register(DepositPledgeCollateral)
class DepositPledgeCollateralAdmin(admin.ModelAdmin):
    list_display = ("account_number", "guarantor_name", "contract", "amount")
    search_fields = ("account_number", "guarantor_name", "contract__contract_number")
    autocomplete_fields = ("contract",)
    filter_horizontal = ("parties",)


@admin.register(OtherCollateral)
class OtherCollateralAdmin(admin.ModelAdmin):
    list_display = ("guarantor_name", "contract", "amount", "returned_date")
    search_fields = ("guarantor_name", "contract__contract_number")
    autocomplete_fields = ("contract",)
    filter_horizontal = ("parties",)


@admin.register(MortgageDeedPropertyIdentifier)
class MortgageDeedPropertyIdentifierAdmin(admin.ModelAdmin):
    list_display = ("identifier", "collateral")
    search_fields = ("identifier", "collateral__mortgage_deed_number")
    autocomplete_fields = ("collateral",)


class DecisionConditionInline(admin.TabularInline):
    model = DecisionCondition
    extra = 0


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "decision_type",
        "decision_maker",
        "decision_date",
        "agreement",
    )
    list_filter = ("decision_type", "decision_maker")
    search_fields = ("title", "diary_number", "agreement__identifier")
    autocomplete_fields = ("agreement",)
    inlines = (DecisionConditionInline,)


@admin.register(DecisionCondition)
class DecisionConditionAdmin(admin.ModelAdmin):
    list_display = ("decision", "condition_type", "supervision_date", "supervised_date")
    list_filter = ("condition_type",)
    search_fields = ("decision__title", "decision__agreement__identifier")
    autocomplete_fields = ("decision",)


@admin.register(AgreementSite)
class AgreementSiteAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "agreement",
        "intended_use",
        "area_m2",
        "floor_area_kem2",
    )
    list_filter = ("intended_use", "preservation_designation", "has_housing_obligation")
    search_fields = ("identifier", "agreement__identifier")
    autocomplete_fields = ("agreement", "intended_use")
    filter_horizontal = ("tenure_types",)


@admin.register(DetailedPlanSite)
class DetailedPlanSiteAdmin(admin.ModelAdmin):
    list_display = ("identifier",)
    search_fields = ("identifier",)
    filter_horizontal = ("agreements",)


@admin.register(SiteIntendedUse)
class SiteIntendedUseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SiteTenureType)
class SiteTenureTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


class PaymentScheduleInstallmentInline(admin.TabularInline):
    model = PaymentScheduleInstallment
    extra = 0
    show_change_link = True


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "agreement",
        "contract",
        "recipient_party",
        "status",
        "signing_date",
    )
    list_filter = ("status",)
    search_fields = (
        "agreement__identifier",
        "contract__contract_number",
        "recipient_party__name",
    )
    autocomplete_fields = ("agreement", "contract", "recipient_party")
    inlines = (PaymentScheduleInstallmentInline,)


class PaymentScheduleInstallmentItemInline(admin.TabularInline):
    model = PaymentScheduleInstallmentItem
    extra = 0


@admin.register(PaymentScheduleInstallment)
class PaymentScheduleInstallmentAdmin(admin.ModelAdmin):
    list_display = ("payment_schedule", "installment_sequence_number", "due_date")
    search_fields = ("payment_schedule__agreement__identifier",)
    autocomplete_fields = ("payment_schedule",)
    inlines = (PaymentScheduleInstallmentItemInline,)


@admin.register(PaymentScheduleInstallmentItem)
class PaymentScheduleInstallmentItemAdmin(admin.ModelAdmin):
    list_display = ("installment", "item_type", "amount")
    list_filter = ("item_type",)
    autocomplete_fields = ("installment",)


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class ShadowSalesLedgerEntryInline(admin.TabularInline):
    model = ShadowSalesLedgerEntry
    extra = 0


class InvoiceRecipientSnapshotInline(admin.StackedInline):
    model = InvoiceRecipientSnapshot
    extra = 0
    max_num = 1
    can_delete = False
    readonly_fields = (
        "party_type",
        "ownership_share_numerator",
        "ownership_share_denominator",
        "name",
        "national_identification_number",
        "business_id",
        "language",
        "street_address",
        "postal_code",
        "city",
        "country",
        "care_of",
        "phone",
        "email",
        "note",
        "ovt_code",
        "sap_customer_number",
        "customer_reference",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_identifier",
        "agreement",
        "recipient_party",
        "due_date",
        "status",
        "billed_amount",
        "sent_at",
    )
    list_filter = ("status", "invoice_type", "sent_at")
    search_fields = (
        "invoice_identifier",
        "agreement__identifier",
        "recipient_party__name",
    )
    autocomplete_fields = (
        "agreement",
        "recipient_party",
        "source_payment_schedule_installment",
    )
    readonly_fields = ("sap_xml", "sent_at", "created_at", "modified_at")
    inlines = (
        InvoiceRecipientSnapshotInline,
        InvoiceItemInline,
        ShadowSalesLedgerEntryInline,
    )


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "item_type", "amount")
    list_filter = ("item_type",)
    autocomplete_fields = ("invoice",)


@admin.register(ShadowSalesLedgerEntry)
class ShadowSalesLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("invoice", "paid_amount", "paid_date", "filing_code")
    list_filter = ("paid_date",)
    search_fields = ("invoice__invoice_identifier", "filing_code")
    autocomplete_fields = ("invoice",)


@admin.register(InvoiceRecipientSnapshot)
class InvoiceRecipientSnapshotAdmin(admin.ModelAdmin):
    list_display = ("invoice", "name", "business_id", "email")
    search_fields = ("invoice__invoice_identifier", "name", "business_id")
    autocomplete_fields = ("invoice",)
    readonly_fields = (
        "invoice",
        "party_type",
        "ownership_share_numerator",
        "ownership_share_denominator",
        "name",
        "national_identification_number",
        "business_id",
        "language",
        "street_address",
        "postal_code",
        "city",
        "country",
        "care_of",
        "phone",
        "email",
        "note",
        "ovt_code",
        "sap_customer_number",
        "customer_reference",
    )


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "agreement_party")
    search_fields = ("name", "email", "agreement_party__name")
    autocomplete_fields = ("agreement_party",)


@admin.register(BillingDetails)
class BillingDetailsAdmin(admin.ModelAdmin):
    list_display = ("agreement_party", "sap_customer_number", "customer_reference")
    search_fields = ("sap_customer_number", "agreement_party__name")
    autocomplete_fields = ("agreement_party",)


@admin.register(InvoiceRecipient)
class InvoiceRecipientAdmin(admin.ModelAdmin):
    list_display = ("name", "business_id", "email", "agreement_party")
    search_fields = ("name", "business_id", "email", "agreement_party__name")
    autocomplete_fields = ("agreement_party",)
