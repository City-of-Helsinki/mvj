from django.db import transaction
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
    party = serializers.SerializerMethodField()
    zoning_plan_number = serializers.CharField(
        source="detailed_plan.plan_number", read_only=True, default=""
    )
    site = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    def get_party(self, agreement):
        return ", ".join(party.name for party in agreement.parties.all() if party.name)

    def get_site(self, agreement):
        return ", ".join(
            site.identifier
            for site in agreement.compensation_sites.all()
            if site.identifier
        )

    class Meta:
        model = LandUseAgreement
        fields = (
            "id",
            "identifier",
            "district",
            "party",
            "zoning_plan_number",
            "site",
            "is_promotion_area",
            "status",
            "status_label",
            "estimated_presentation_year",
            "estimated_payment_year",
            "created_at",
            "modified_at",
        )


class LandUseAgreementSerializer(serializers.ModelSerializer):
    addresses = AgreementAddressSerializer(many=True, required=False)
    preparers = AgreementPreparerSerializer(many=True, required=False)

    class Meta:
        model = LandUseAgreement
        fields = (
            "id",
            "identifier",
            "district",
            "is_promotion_area",
            "status",
            "estimated_presentation_year",
            "estimated_payment_year",
            "includes_housing_obligations",
            "obligations_deadline",
            "authorized_signatory",
            "addresses",
            "preparers",
            "detailed_plan",
            "detailed_plan_sites",
            "collateral_multiplier",
            "created_at",
            "modified_at",
        )
        read_only_fields = ("id", "identifier", "created_at", "modified_at")

    @transaction.atomic
    def create(self, validated_data):
        addresses = validated_data.pop("addresses", [])
        preparers = validated_data.pop("preparers", [])
        district = validated_data.get("district")
        if district is None:
            raise serializers.ValidationError({"district": "This field is required."})

        district = District.objects.select_for_update().get(pk=district.pk)
        prefix = f"MA1{district.identifier.zfill(2)}-"
        existing_identifiers = LandUseAgreement.objects.filter(
            identifier__startswith=prefix
        ).values_list("identifier", flat=True)
        sequence_numbers = [
            int(identifier.removeprefix(prefix))
            for identifier in existing_identifiers
            if identifier.removeprefix(prefix).isdigit()
        ]
        validated_data["identifier"] = f"{prefix}{max(sequence_numbers, default=0) + 1}"
        agreement = super().create(validated_data)
        self._replace_summary_relations(agreement, addresses, preparers)
        return agreement

    @transaction.atomic
    def update(self, instance, validated_data):
        addresses = validated_data.pop("addresses", None)
        preparers = validated_data.pop("preparers", None)
        agreement = super().update(instance, validated_data)
        self._replace_summary_relations(agreement, addresses, preparers)
        return agreement

    def _replace_summary_relations(self, agreement, addresses, preparers):
        if addresses is not None:
            agreement.addresses.all().delete()
            AgreementAddress.objects.bulk_create(
                [
                    AgreementAddress(agreement=agreement, **address)
                    for address in addresses
                ]
            )
        if preparers is not None:
            agreement.preparers.all().delete()
            AgreementPreparer.objects.bulk_create(
                [
                    AgreementPreparer(agreement=agreement, **preparer)
                    for preparer in preparers
                ]
            )


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
            "detailed_plan_sites",
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


class CountryCodeField(serializers.ChoiceField):
    def to_representation(self, value):
        return super().to_representation(str(value))


class InvoiceRecipientSerializer(serializers.ModelSerializer):
    country = CountryCodeField(
        choices=InvoiceRecipient._meta.get_field("country").get_choices(),
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = InvoiceRecipient
        fields = (
            "id",
            "party_type",
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
        )


class AgreementPartySerializer(serializers.ModelSerializer):
    country = serializers.CharField()
    contact_persons = ContactPersonSerializer(many=True, read_only=True)
    billing_details = BillingDetailsSerializer(read_only=True)
    invoice_recipient = serializers.SerializerMethodField()

    class Meta:
        model = AgreementParty
        fields = (
            "id",
            "party_type",
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
            "role",
            "contact_persons",
            "billing_details",
            "invoice_recipient",
        )

    def get_invoice_recipient(self, party):
        try:
            recipient = InvoiceRecipient.objects.get(agreement_party=party)
        except InvoiceRecipient.DoesNotExist:
            return None
        return InvoiceRecipientSerializer(recipient).data


class AgreementPartyWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact_persons = ContactPersonSerializer(many=True, required=False)
    billing_details = BillingDetailsSerializer(required=False, allow_null=True)
    invoice_recipient = InvoiceRecipientSerializer(required=False, allow_null=True)

    class Meta:
        model = AgreementParty
        fields = (
            "id",
            "party_type",
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
            "role",
            "contact_persons",
            "billing_details",
            "invoice_recipient",
        )


class LandPolicyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandPolicyProgram
        fields = ("id", "name", "default_discount_percentage")


class LandUseCompensationSerializer(serializers.ModelSerializer):
    land_policy_program = LandPolicyProgramSerializer(read_only=True)

    class Meta:
        model = LandUseCompensation
        fields = (
            "id",
            "created_at",
            "modified_at",
            "excel_calculation_url",
            "monetary_compensation",
            "land_compensation",
            "other_compensation",
            "total_compensation",
            "base_price",
            "land_compensation_description",
            "other_compensation_description",
            "value_before_detailed_plan_proposal",
            "demolition_or_other_deduction",
            "land_use_compensation",
            "land_policy_program",
            "land_policy_program_discount_percentage",
            "public_areas_m2",
            "public_areas_acquisition_value",
        )


class LandUseCompensationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseCompensation
        fields = (
            "excel_calculation_url",
            "monetary_compensation",
            "land_compensation",
            "other_compensation",
            "total_compensation",
            "base_price",
            "land_compensation_description",
            "other_compensation_description",
            "value_before_detailed_plan_proposal",
            "demolition_or_other_deduction",
            "land_use_compensation",
            "land_policy_program",
            "land_policy_program_discount_percentage",
            "public_areas_m2",
            "public_areas_acquisition_value",
        )


class SiteIntendedUseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteIntendedUse
        fields = ("id", "name")


class SiteTenureTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteTenureType
        fields = ("id", "name")


class AgreementSiteSerializer(serializers.ModelSerializer):
    intended_use = SiteIntendedUseSerializer(read_only=True)
    tenure_types = SiteTenureTypeSerializer(many=True, read_only=True)

    class Meta:
        model = AgreementSite
        fields = (
            "id",
            "created_at",
            "modified_at",
            "identifier",
            "area_m2",
            "floor_area_kem2",
            "intended_use",
            "tenure_types",
            "preservation_designation",
            "has_housing_obligation",
            "unit_price_euro_per_kem2",
        )


class AgreementSiteWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = AgreementSite
        fields = (
            "id",
            "identifier",
            "area_m2",
            "floor_area_kem2",
            "intended_use",
            "tenure_types",
            "preservation_designation",
            "has_housing_obligation",
            "unit_price_euro_per_kem2",
        )


class CompensationWithSitesWriteSerializer(serializers.Serializer):
    compensation = LandUseCompensationWriteSerializer()
    sites = AgreementSiteWriteSerializer(many=True)


class DecisionConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionCondition
        fields = (
            "id",
            "created_at",
            "modified_at",
            "condition_type",
            "supervision_date",
            "supervised_date",
            "note",
        )


class DecisionSerializer(serializers.ModelSerializer):
    conditions = DecisionConditionSerializer(many=True, read_only=True)

    class Meta:
        model = Decision
        fields = (
            "id",
            "created_at",
            "modified_at",
            "title",
            "decision_maker",
            "decision_date",
            "section",
            "decision_type",
            "diary_number",
            "note",
            "conditions",
        )


class DecisionConditionWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = DecisionCondition
        fields = (
            "id",
            "condition_type",
            "supervision_date",
            "supervised_date",
            "note",
        )


class DecisionWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    conditions = DecisionConditionWriteSerializer(many=True, required=False)

    class Meta:
        model = Decision
        fields = (
            "id",
            "title",
            "decision_maker",
            "decision_date",
            "section",
            "decision_type",
            "diary_number",
            "note",
            "conditions",
        )


class ContractChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractChange
        fields = (
            "id",
            "identifier",
            "signing_date",
            "signing_deadline",
            "first_invitation_sent_date",
            "second_invitation_sent_date",
            "third_invitation_sent_date",
            "executor",
            "decision",
            "note",
        )


class MortgageDeedPropertyIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = MortgageDeedPropertyIdentifier
        fields = ("id", "identifier")


class CollateralSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "guarantee_type",
            "parties",
            "third_party_pledger_name",
            "third_party_pledger_business_id",
            "start_date",
            "end_date",
            "amount",
            "returned_date",
            "marked_returned_by",
            "additional_information",
        )


class MortgageDeedCollateralSerializer(CollateralSerializer):
    property_identifiers = MortgageDeedPropertyIdentifierSerializer(
        many=True, read_only=True
    )

    class Meta(CollateralSerializer.Meta):
        model = MortgageDeedCollateral
        fields = (
            *CollateralSerializer.Meta.fields,
            "document_category",
            "target",
            "facility_identifier",
            "mortgage_deed_number",
            "mortgage_deed_date",
            "subsequent_pledgee_name",
            "subsequent_pledgee_business_id",
            "property_identifiers",
        )


class CashDepositCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = CashDepositCollateral
        fields = (
            *CollateralSerializer.Meta.fields,
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "account_number",
            "paid_at_date",
        )


class PersonalGuaranteeCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = PersonalGuaranteeCollateral
        fields = (
            *CollateralSerializer.Meta.fields,
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "guarantee_identifier",
        )


class DepositPledgeCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = DepositPledgeCollateral
        fields = (
            *CollateralSerializer.Meta.fields,
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "account_number",
        )


class OtherCollateralSerializer(CollateralSerializer):
    class Meta(CollateralSerializer.Meta):
        model = OtherCollateral
        fields = (
            *CollateralSerializer.Meta.fields,
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
        )


class ContractSerializer(serializers.ModelSerializer):
    changes = ContractChangeSerializer(many=True, read_only=True)
    mortgage_deed_collaterals = MortgageDeedCollateralSerializer(
        many=True,
        read_only=True,
        source="mortgagedeedcollateral_collaterals",
    )
    cash_deposit_collaterals = CashDepositCollateralSerializer(
        many=True,
        read_only=True,
        source="cashdepositcollateral_collaterals",
    )
    personal_guarantee_collaterals = PersonalGuaranteeCollateralSerializer(
        many=True,
        read_only=True,
        source="personalguaranteecollateral_collaterals",
    )
    deposit_pledge_collaterals = DepositPledgeCollateralSerializer(
        many=True,
        read_only=True,
        source="depositpledgecollateral_collaterals",
    )
    other_collaterals = OtherCollateralSerializer(
        many=True,
        read_only=True,
        source="othercollateral_collaterals",
    )

    class Meta:
        model = Contract
        fields = (
            "id",
            "identifier",
            "signing_date",
            "signing_deadline",
            "first_invitation_sent_date",
            "second_invitation_sent_date",
            "third_invitation_sent_date",
            "executor",
            "decision",
            "note",
            "title",
            "contract_type",
            "changes",
            "mortgage_deed_collaterals",
            "cash_deposit_collaterals",
            "personal_guarantee_collaterals",
            "deposit_pledge_collaterals",
            "other_collaterals",
        )


class ContractChangeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ContractChange
        fields = (
            "id",
            "identifier",
            "signing_date",
            "signing_deadline",
            "first_invitation_sent_date",
            "second_invitation_sent_date",
            "third_invitation_sent_date",
            "executor",
            "decision",
            "note",
        )


class CollateralWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    guarantee_type = serializers.CharField()
    parties = serializers.ListField(child=serializers.IntegerField(), required=False)
    third_party_pledger_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    third_party_pledger_business_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    amount = serializers.DecimalField(
        max_digits=20, decimal_places=2, required=False, allow_null=True
    )
    returned_date = serializers.DateField(required=False, allow_null=True)
    marked_returned_by = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    additional_information = serializers.CharField(required=False, allow_blank=True)
    document_category = serializers.CharField(required=False, allow_blank=True)
    target = serializers.CharField(required=False, allow_blank=True)
    property_identifiers = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    facility_identifier = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    mortgage_deed_number = serializers.CharField(required=False, allow_blank=True)
    mortgage_deed_date = serializers.DateField(required=False, allow_null=True)
    subsequent_pledgee_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    subsequent_pledgee_business_id = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    guarantor_name = serializers.CharField(required=False, allow_blank=True)
    guarantor_business_id = serializers.CharField(required=False, allow_blank=True)
    guarantor_national_identification_number = serializers.CharField(
        required=False, allow_blank=True
    )
    guarantee_identifier = serializers.CharField(required=False, allow_blank=True)
    account_number = serializers.CharField(required=False, allow_blank=True)
    paid_at_date = serializers.DateField(required=False, allow_null=True)


class ContractWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    changes = ContractChangeWriteSerializer(many=True, required=False)
    collaterals = CollateralWriteSerializer(many=True, required=False)

    class Meta:
        model = Contract
        fields = (
            "id",
            "identifier",
            "signing_date",
            "signing_deadline",
            "first_invitation_sent_date",
            "second_invitation_sent_date",
            "third_invitation_sent_date",
            "executor",
            "decision",
            "note",
            "title",
            "contract_type",
            "changes",
            "collaterals",
        )


class PaymentScheduleInstallmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentScheduleInstallmentItem
        fields = (
            "id",
            "created_at",
            "modified_at",
            "item_type",
            "description",
            "amount",
        )


class PaymentScheduleInstallmentSerializer(serializers.ModelSerializer):
    items = PaymentScheduleInstallmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentScheduleInstallment
        fields = (
            "id",
            "created_at",
            "modified_at",
            "installment_sequence_number",
            "installment_count_total",
            "due_date",
            "interest_calculation_period_start_date",
            "interest_calculation_period_end_date",
            "items",
        )


class PaymentScheduleSerializer(serializers.ModelSerializer):
    installments = PaymentScheduleInstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentSchedule
        fields = (
            "id",
            "created_at",
            "modified_at",
            "recipient_party",
            "contract",
            "status",
            "rejected_reason",
            "signing_date",
            "increase_percentage",
            "base_interest_rate",
            "interest_margin",
            "installments",
        )
        read_only_fields = ("status", "rejected_reason")


class PaymentScheduleInstallmentItemWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PaymentScheduleInstallmentItem
        fields = ("id", "item_type", "description", "amount")


class PaymentScheduleInstallmentWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    items = PaymentScheduleInstallmentItemWriteSerializer(many=True)

    class Meta:
        model = PaymentScheduleInstallment
        fields = (
            "id",
            "installment_sequence_number",
            "installment_count_total",
            "due_date",
            "interest_calculation_period_start_date",
            "interest_calculation_period_end_date",
            "items",
        )


class PaymentScheduleWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    installments = PaymentScheduleInstallmentWriteSerializer(many=True)

    class Meta:
        model = PaymentSchedule
        fields = (
            "id",
            "recipient_party",
            "contract",
            "signing_date",
            "increase_percentage",
            "base_interest_rate",
            "interest_margin",
            "installments",
        )


class PaymentScheduleRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False)


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = (
            "id",
            "created_at",
            "modified_at",
            "item_type",
            "description",
            "amount",
        )


class ShadowSalesLedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShadowSalesLedgerEntry
        fields = (
            "id",
            "created_at",
            "modified_at",
            "paid_amount",
            "paid_date",
            "filing_code",
        )


class InvoiceRecipientSnapshotSerializer(serializers.ModelSerializer):
    country = serializers.CharField()

    class Meta:
        model = InvoiceRecipientSnapshot
        fields = (
            "id",
            "party_type",
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
            "sap_xml",
            "created_at",
            "modified_at",
            "remaining_amount",
            "recipient_snapshot",
            "items",
            "payments",
        )
        read_only_fields = fields
