from rest_framework import serializers

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


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ("id", "name", "identifier")


class AuthorizedSignatorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizedSignatory
        fields = ("id", "name")


class DetailedPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailedPlan
        fields = (
            "id",
            "plan_number",
            "processing_stage",
            "approval_date",
            "effective_date",
            "approver",
            "diary_number",
        )


class AgreementAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgreementAddress
        fields = ("id", "street_address", "postal_code", "city")


class AgreementPreparerSerializer(serializers.ModelSerializer):
    preparer_name = serializers.CharField(
        source="preparer.get_full_name", read_only=True
    )

    class Meta:
        model = AgreementPreparer
        fields = ("id", "preparer", "preparer_name")


class LandUseAgreementListSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)

    class Meta:
        model = LandUseAgreement
        fields = (
            "id",
            "identifier",
            "agreement_type",
            "district",
            "status",
            "estimated_presentation_year",
            "estimated_payment_year",
            "created_at",
            "modified_at",
        )


class LandUseAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreement
        fields = (
            "id",
            "identifier",
            "agreement_type",
            "district",
            "is_promotion_area",
            "status",
            "estimated_presentation_year",
            "estimated_payment_year",
            "includes_housing_obligations",
            "obligations_deadline",
            "authorized_signatory",
            "detailed_plan",
            "collateral_multiplier",
            "created_at",
            "modified_at",
        )
        read_only_fields = ("id", "created_at", "modified_at")


class LandUseAgreementOverviewSerializer(LandUseAgreementListSerializer):
    authorized_signatory = AuthorizedSignatorySerializer(read_only=True)
    detailed_plan = DetailedPlanSerializer(read_only=True)
    addresses = AgreementAddressSerializer(many=True, read_only=True)
    preparers = AgreementPreparerSerializer(many=True, read_only=True)

    class Meta:
        model = LandUseAgreement
        fields = (
            *LandUseAgreementListSerializer.Meta.fields,
            "is_promotion_area",
            "includes_housing_obligations",
            "obligations_deadline",
            "authorized_signatory",
            "detailed_plan",
            "collateral_multiplier",
            "addresses",
            "preparers",
        )


class ContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPerson
        fields = ("id", "name", "phone", "email")


class BillingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingDetails
        fields = ("id", "ovt_code", "sap_customer_number", "customer_reference")


class InvoiceRecipientSerializer(serializers.ModelSerializer):
    country = serializers.CharField()

    class Meta:
        model = InvoiceRecipient
        exclude = ("agreement_party",)


class AgreementPartySerializer(serializers.ModelSerializer):
    country = serializers.CharField()
    contact_persons = ContactPersonSerializer(many=True, read_only=True)
    billing_details = BillingDetailsSerializer(read_only=True)
    invoice_recipient = serializers.SerializerMethodField()

    class Meta:
        model = AgreementParty
        exclude = ("agreement",)

    def get_invoice_recipient(self, party):
        try:
            recipient = InvoiceRecipient.objects.get(agreement_party=party)
        except InvoiceRecipient.DoesNotExist:
            return None
        return InvoiceRecipientSerializer(recipient).data


class LandPolicyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandPolicyProgram
        fields = ("id", "name", "default_discount_percentage")


class LandUseCompensationSerializer(serializers.ModelSerializer):
    land_policy_program = LandPolicyProgramSerializer(read_only=True)

    class Meta:
        model = LandUseCompensation
        exclude = ("agreement",)


class SiteIntendedUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteIntendedUse
        fields = ("id", "name")


class SiteTenureTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteTenureType
        fields = ("id", "name")


class DetailedPlanSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetailedPlanSite
        fields = ("id", "identifier")


class AgreementSiteSerializer(serializers.ModelSerializer):
    intended_use = SiteIntendedUseSerializer(read_only=True)
    tenure_types = SiteTenureTypeSerializer(many=True, read_only=True)

    class Meta:
        model = AgreementSite
        exclude = ("agreement",)


class DecisionConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionCondition
        exclude = ("decision",)


class DecisionSerializer(serializers.ModelSerializer):
    conditions = DecisionConditionSerializer(many=True, read_only=True)

    class Meta:
        model = Decision
        exclude = ("agreement",)


class ContractChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractChange
        exclude = ("contract",)


class MortgageDeedPropertyIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageDeedPropertyIdentifier
        fields = ("id", "identifier")


class CollateralSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ("contract",)


class MortgageDeedCollateralSerializer(CollateralSerializer):
    property_identifiers = MortgageDeedPropertyIdentifierSerializer(
        many=True, read_only=True
    )

    class Meta(CollateralSerializer.Meta):
        model = MortgageDeedCollateral


class CashDepositCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = CashDepositCollateral


class PersonalGuaranteeCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = PersonalGuaranteeCollateral


class DepositPledgeCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = DepositPledgeCollateral


class OtherCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = OtherCollateral


class ContractSerializer(serializers.ModelSerializer):
    changes = ContractChangeSerializer(many=True, read_only=True)
    mortgage_deed_collaterals = MortgageDeedCollateralSerializer(
        many=True, read_only=True
    )
    cash_deposit_collaterals = CashDepositCollateralSerializer(
        many=True, read_only=True
    )
    personal_guarantee_collaterals = PersonalGuaranteeCollateralSerializer(
        many=True, read_only=True
    )
    deposit_pledge_collaterals = DepositPledgeCollateralSerializer(
        many=True, read_only=True
    )
    other_collaterals = OtherCollateralSerializer(many=True, read_only=True)

    class Meta:
        model = Contract
        exclude = ("agreement",)


class PaymentScheduleInstallmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentScheduleInstallmentItem
        exclude = ("installment",)


class PaymentScheduleInstallmentSerializer(serializers.ModelSerializer):
    items = PaymentScheduleInstallmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentScheduleInstallment
        exclude = ("payment_schedule",)


class PaymentScheduleSerializer(serializers.ModelSerializer):
    installments = PaymentScheduleInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentSchedule
        exclude = ("agreement",)
        read_only_fields = ("status", "rejected_reason")


class PaymentScheduleRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        exclude = ("invoice",)


class ShadowSalesLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowSalesLedgerEntry
        exclude = ("invoice",)


class InvoiceRecipientSnapshotSerializer(serializers.ModelSerializer):
    country = serializers.CharField()

    class Meta:
        model = InvoiceRecipientSnapshot
        exclude = ("invoice",)


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = ShadowSalesLedgerEntrySerializer(many=True, read_only=True)
    recipient_snapshot = InvoiceRecipientSnapshotSerializer(read_only=True)
    remaining_amount = serializers.DecimalField(
        source="get_remaining_amount", max_digits=20, decimal_places=2, read_only=True
    )

    class Meta:
        model = Invoice
        fields = (
            "id",
            "agreement",
            "source_payment_schedule_installment",
            "recipient_party",
            "installment_sequence_number",
            "installment_count_total",
            "due_date",
            "invoice_identifier",
            "invoice_type",
            "status",
            "sent_at",
            "billed_amount",
            "created_at",
            "modified_at",
            "remaining_amount",
            "recipient_snapshot",
            "items",
            "payments",
        )
        read_only_fields = fields
