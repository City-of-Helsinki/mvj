from functools import partial

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import serializers
from rest_framework.exceptions import APIException

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


class ReferencedResourceConflict(APIException):
    status_code = 409
    default_code = "referenced_resource"


def set_one_to_one(model, parent_field, parent, data):
    lookup = {parent_field: parent}
    if data is None:
        model.objects.filter(**lookup).delete()
    else:
        model.objects.update_or_create(**lookup, defaults=data)


def sync_rows(queryset, rows, save_row):
    """Updates rows listed with an id, creates the others, and deletes unlisted rows."""
    existing = {row.pk: row for row in queryset.select_for_update(of=("self",))}
    saved_ids = []
    for data in rows:
        row_id = data.pop("id", None)
        if row_id is not None and row_id not in existing:
            raise serializers.ValidationError(
                {"id": f"Item {row_id} does not belong to this parent."}
            )
        saved_ids.append(save_row(existing.get(row_id), data).pk)
    queryset.exclude(pk__in=saved_ids).delete()
    return saved_ids


def save_children(model, parent_field, parent, rows):
    def save_row(obj, data):
        if obj is None:
            return model.objects.create(**{parent_field: parent}, **data)
        for field, value in data.items():
            setattr(obj, field, value)
        obj.save()
        return obj

    sync_rows(model.objects.filter(**{parent_field: parent}), rows, save_row)


class ReplaceListSerializer(serializers.ListSerializer):
    conflict_code = "referenced_resource"
    conflict_detail = "Remove references before deleting these rows."
    read_related = ()
    read_prefetch = ()

    @transaction.atomic
    def update(self, instance, validated_data):
        self.check_replacement(instance, validated_data)
        try:
            saved_ids = sync_rows(instance, validated_data, self.save_item)
        except ProtectedError as error:
            raise ReferencedResourceConflict(
                {"code": self.conflict_code, "detail": self.conflict_detail}
            ) from error
        return (
            self.child.Meta.model.objects.filter(pk__in=saved_ids)
            .select_related(*self.read_related)
            .prefetch_related(*self.read_prefetch)
        )

    def check_replacement(self, instance, validated_data):
        """Runs reference and status checks before any write."""

    def save_item(self, obj, data):
        if obj is None:
            return self.child.create(data)
        return self.child.update(obj, data)


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


class ContactPersonWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

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


class AgreementPartyListSerializer(ReplaceListSerializer):
    conflict_code = "referenced_parties"
    conflict_detail = "Remove financial references before deleting these parties."
    read_prefetch = ("contact_persons", "billing_details")

    def check_replacement(self, instance, validated_data):
        retained_ids = {attrs.get("id") for attrs in validated_data}
        removed_ids = set(instance.values_list("pk", flat=True)) - retained_ids
        referenced_ids = set(
            PaymentSchedule.objects.filter(
                recipient_party_id__in=removed_ids
            ).values_list("recipient_party_id", flat=True)
        ) | set(
            Invoice.objects.filter(recipient_party_id__in=removed_ids).values_list(
                "recipient_party_id", flat=True
            )
        )
        if referenced_ids:
            raise ReferencedResourceConflict(
                {
                    "code": self.conflict_code,
                    "ids": sorted(referenced_ids),
                    "detail": self.conflict_detail,
                }
            )


class AgreementPartyWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact_persons = ContactPersonWriteSerializer(many=True, required=False)
    billing_details = BillingDetailsSerializer(required=False, allow_null=True)
    invoice_recipient = InvoiceRecipientSerializer(required=False, allow_null=True)

    class Meta:
        model = AgreementParty
        list_serializer_class = AgreementPartyListSerializer
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

    @transaction.atomic
    def create(self, validated_data):
        nested = self._pop_nested(validated_data)
        party = super().create(validated_data)
        self._save_nested(party, **nested)
        return party

    @transaction.atomic
    def update(self, instance, validated_data):
        nested = self._pop_nested(validated_data)
        party = super().update(instance, validated_data)
        self._save_nested(party, **nested)
        return party

    def _pop_nested(self, validated_data):
        return {
            "contact_persons": validated_data.pop("contact_persons", []),
            "billing_details": validated_data.pop("billing_details", None),
            "invoice_recipient": validated_data.pop("invoice_recipient", None),
        }

    def _save_nested(self, party, contact_persons, billing_details, invoice_recipient):
        save_children(ContactPerson, "agreement_party", party, contact_persons)
        set_one_to_one(BillingDetails, "agreement_party", party, billing_details)
        set_one_to_one(InvoiceRecipient, "agreement_party", party, invoice_recipient)


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


class AgreementSiteListSerializer(ReplaceListSerializer):
    read_related = ("intended_use",)
    read_prefetch = ("tenure_types",)


class AgreementSiteWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = AgreementSite
        list_serializer_class = AgreementSiteListSerializer
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

    def create(self, validated_data):
        tenure_types = validated_data.pop("tenure_types", [])
        site = super().create(validated_data)
        site.tenure_types.set(tenure_types)
        return site

    def update(self, instance, validated_data):
        tenure_types = validated_data.pop("tenure_types", [])
        site = super().update(instance, validated_data)
        site.tenure_types.set(tenure_types)
        return site


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


class DecisionListSerializer(ReplaceListSerializer):
    conflict_code = "referenced_decisions"
    conflict_detail = "Unlink contracts before deleting these decisions."
    read_prefetch = ("conditions",)

    def check_replacement(self, instance, validated_data):
        retained_ids = {attrs.get("id") for attrs in validated_data}
        removed_ids = set(instance.values_list("pk", flat=True)) - retained_ids
        referenced_ids = set(
            Contract.objects.filter(decision_id__in=removed_ids).values_list(
                "decision_id", flat=True
            )
        )
        referenced_ids.update(
            ContractChange.objects.filter(decision_id__in=removed_ids).values_list(
                "decision_id", flat=True
            )
        )
        if referenced_ids:
            raise ReferencedResourceConflict(
                {
                    "code": self.conflict_code,
                    "ids": sorted(referenced_ids),
                    "detail": self.conflict_detail,
                }
            )


class DecisionWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    conditions = DecisionConditionWriteSerializer(many=True, required=False)

    class Meta:
        model = Decision
        list_serializer_class = DecisionListSerializer
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

    def create(self, validated_data):
        conditions = validated_data.pop("conditions", [])
        decision = super().create(validated_data)
        save_children(DecisionCondition, "decision", decision, conditions)
        return decision

    def update(self, instance, validated_data):
        conditions = validated_data.pop("conditions", [])
        decision = super().update(instance, validated_data)
        save_children(DecisionCondition, "decision", decision, conditions)
        return decision


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


class CollateralWriteBaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            not_applicable = {
                key: "Not applicable to this collateral type."
                for key, value in data.items()
                if key not in self.fields and value not in (None, "", [])
            }
            if not_applicable:
                raise serializers.ValidationError(not_applicable)
        return super().to_internal_value(data)


class MortgageDeedCollateralWriteSerializer(CollateralWriteBaseSerializer):
    guarantee_type = serializers.HiddenField(
        default=MortgageDeedCollateral.CollateralType.MORTGAGE_DEED
    )

    class Meta:
        model = MortgageDeedCollateral
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
            "document_category",
            "target",
            "facility_identifier",
            "mortgage_deed_number",
            "mortgage_deed_date",
            "subsequent_pledgee_name",
            "subsequent_pledgee_business_id",
            "property_identifiers",
        )
        extra_kwargs = {
            "mortgage_deed_number": {"required": False, "allow_blank": True},
            "mortgage_deed_date": {"required": False, "allow_null": True},
        }


class CashDepositCollateralWriteSerializer(CollateralWriteBaseSerializer):
    guarantee_type = serializers.HiddenField(
        default=CashDepositCollateral.CollateralType.CASH_DEPOSIT
    )

    class Meta:
        model = CashDepositCollateral
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
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "account_number",
            "paid_at_date",
        )


class PersonalGuaranteeCollateralWriteSerializer(CollateralWriteBaseSerializer):
    guarantee_type = serializers.HiddenField(
        default=PersonalGuaranteeCollateral.CollateralType.PERSONAL_GUARANTEE
    )

    class Meta:
        model = PersonalGuaranteeCollateral
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
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "guarantee_identifier",
        )


class DepositPledgeCollateralWriteSerializer(CollateralWriteBaseSerializer):
    guarantee_type = serializers.HiddenField(
        default=DepositPledgeCollateral.CollateralType.DEPOSIT_PLEDGE
    )

    class Meta:
        model = DepositPledgeCollateral
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
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
            "account_number",
        )


class OtherCollateralWriteSerializer(CollateralWriteBaseSerializer):
    guarantee_type = serializers.HiddenField(
        default=OtherCollateral.CollateralType.OTHER
    )

    class Meta:
        model = OtherCollateral
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
            "document_category",
            "guarantor_name",
            "guarantor_business_id",
            "guarantor_national_identification_number",
        )


class ContractListSerializer(ReplaceListSerializer):
    read_prefetch = (
        "changes",
        "mortgagedeedcollateral_collaterals__parties",
        "cashdepositcollateral_collaterals__parties",
        "personalguaranteecollateral_collaterals__parties",
        "depositpledgecollateral_collaterals__parties",
        "othercollateral_collaterals__parties",
    )

    def check_replacement(self, instance, validated_data):
        if not validated_data:
            return
        agreement = validated_data[0]["agreement"]
        decision_ids = set()
        party_ids = set()
        for contract in validated_data:
            records = [contract, *contract.get("changes", [])]
            decision_ids |= {r["decision"].pk for r in records if r.get("decision")}
            for key in ContractWriteSerializer.COLLATERAL_MODELS:
                for collateral in contract.get(key, []):
                    party_ids |= {party.pk for party in collateral.get("parties", [])}
        valid_decision_ids = set(
            agreement.decisions.filter(pk__in=decision_ids).values_list("pk", flat=True)
        )
        if decision_ids != valid_decision_ids:
            raise serializers.ValidationError(
                {"decision": "Contract decisions must belong to this agreement."}
            )
        valid_party_ids = set(agreement.parties.values_list("pk", flat=True))
        if not party_ids <= valid_party_ids:
            raise serializers.ValidationError(
                {"parties": "Collateral parties must belong to this agreement."}
            )


class ContractWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    changes = ContractChangeWriteSerializer(many=True, required=False)
    mortgage_deed_collaterals = MortgageDeedCollateralWriteSerializer(
        many=True, required=False
    )
    cash_deposit_collaterals = CashDepositCollateralWriteSerializer(
        many=True, required=False
    )
    personal_guarantee_collaterals = PersonalGuaranteeCollateralWriteSerializer(
        many=True, required=False
    )
    deposit_pledge_collaterals = DepositPledgeCollateralWriteSerializer(
        many=True, required=False
    )
    other_collaterals = OtherCollateralWriteSerializer(many=True, required=False)

    COLLATERAL_MODELS = {
        "mortgage_deed_collaterals": MortgageDeedCollateral,
        "cash_deposit_collaterals": CashDepositCollateral,
        "personal_guarantee_collaterals": PersonalGuaranteeCollateral,
        "deposit_pledge_collaterals": DepositPledgeCollateral,
        "other_collaterals": OtherCollateral,
    }

    class Meta:
        model = Contract
        list_serializer_class = ContractListSerializer
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

    def to_internal_value(self, data):
        if isinstance(data, dict) and "collaterals" in data:
            raise serializers.ValidationError(
                {"collaterals": "Send collaterals under their per-type keys."}
            )
        return super().to_internal_value(data)

    @transaction.atomic
    def create(self, validated_data):
        changes = validated_data.pop("changes", [])
        collaterals = {
            key: validated_data.pop(key, []) for key in self.COLLATERAL_MODELS
        }
        contract = super().create(validated_data)
        self._save_children(contract, changes, collaterals)
        return contract

    @transaction.atomic
    def update(self, instance, validated_data):
        changes = validated_data.pop("changes", [])
        collaterals = {
            key: validated_data.pop(key, []) for key in self.COLLATERAL_MODELS
        }
        contract = super().update(instance, validated_data)
        self._save_children(contract, changes, collaterals)
        return contract

    def _save_children(self, contract, changes, collaterals):
        sync_rows(
            contract.changes.all(),
            changes,
            partial(self._save_change, contract),
        )
        for key, model in self.COLLATERAL_MODELS.items():
            sync_rows(
                model.objects.filter(contract=contract),
                collaterals[key],
                partial(self._save_collateral, contract, model),
            )

    def _save_change(self, contract, change, data):
        if change is None:
            return ContractChange.objects.create(contract=contract, **data)
        for field, value in data.items():
            setattr(change, field, value)
        change.save()
        return change

    def _save_collateral(self, contract, model, collateral, data):
        party_ids = data.pop("parties", [])
        if collateral is None:
            collateral = model(contract=contract, **data)
        else:
            for field, value in data.items():
                setattr(collateral, field, value)
        try:
            collateral.save()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        except ValueError as error:
            raise serializers.ValidationError({"detail": str(error)}) from error
        collateral.parties.set(party_ids)
        return collateral


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


EDITABLE_SCHEDULE_STATUSES = ("DRAFT", "REJECTED")


class PaymentScheduleListSerializer(ReplaceListSerializer):
    read_related = ("recipient_party", "contract")
    read_prefetch = ("installments__items",)

    def check_replacement(self, instance, validated_data):
        retained_ids = {attrs["id"] for attrs in validated_data if "id" in attrs}
        removed = instance.exclude(pk__in=retained_ids).exclude(
            status__in=EDITABLE_SCHEDULE_STATUSES
        )
        if removed.exists():
            raise serializers.ValidationError(
                {"status": "Only draft or rejected schedules can be deleted."}
            )


class PaymentScheduleWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    installments = PaymentScheduleInstallmentWriteSerializer(many=True)

    class Meta:
        model = PaymentSchedule
        list_serializer_class = PaymentScheduleListSerializer
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

    @transaction.atomic
    def create(self, validated_data):
        installments = validated_data.pop("installments")
        self._check_references(validated_data["agreement"], validated_data)
        schedule = super().create(validated_data)
        self._finish(schedule, installments)
        return schedule

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.status not in EDITABLE_SCHEDULE_STATUSES:
            raise serializers.ValidationError(
                {"status": "Only draft or rejected schedules can be edited."}
            )
        installments = validated_data.pop("installments")
        self._check_references(instance.agreement, validated_data)
        schedule = super().update(instance, validated_data)
        self._finish(schedule, installments)
        return schedule

    def _check_references(self, agreement, data):
        if (
            data["recipient_party"].agreement_id != agreement.pk
            or data["contract"].agreement_id != agreement.pk
        ):
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Payment schedule party and contract must belong to "
                        "this agreement."
                    )
                }
            )

    def _finish(self, schedule, installments):
        try:
            schedule.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        schedule.save()

        sequences = [i["installment_sequence_number"] for i in installments]
        if len(sequences) != len(set(sequences)):
            raise serializers.ValidationError(
                {"installments": "Installment sequence numbers must be unique."}
            )
        sync_rows(
            schedule.installments.all(),
            installments,
            lambda obj, data: self._save_installment(schedule, obj, data),
        )

    def _save_installment(self, schedule, installment, data):
        items = data.pop("items")
        if installment is None:
            installment = PaymentScheduleInstallment.objects.create(
                payment_schedule=schedule, **data
            )
        else:
            for field, value in data.items():
                setattr(installment, field, value)
            installment.save()
        sync_rows(
            installment.items.all(),
            items,
            lambda obj, item: self._save_item(installment, obj, item),
        )
        return installment

    def _save_item(self, installment, item, data):
        if item is None:
            return PaymentScheduleInstallmentItem.objects.create(
                installment=installment, **data
            )
        for field, value in data.items():
            setattr(item, field, value)
        item.save()
        return item


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
