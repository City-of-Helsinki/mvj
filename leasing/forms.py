from django import forms
from django.core import validators
from django.core.exceptions import ValidationError

from leasing.enums import (
    InfillDevelopmentCompensationState,
    LeaseState,
    TenantContactType,
)
from leasing.models import Contact, DecisionMaker, District, LeaseType, Municipality
from leasing.validators import validate_business_id


class CommaSeparatedChoiceField(forms.ChoiceField):
    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return []

        value = [item.strip() for item in str(value).split(",") if item.strip()]

        return value

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages["required"], code="required")
        # Validate that each value in the value list is in self.choices.
        for val in value:
            if not self.valid_value(val):
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": val},
                )


class LeaseSearchForm(forms.Form):
    succinct = forms.BooleanField(label="Succinct", required=False)
    identifier = forms.CharField(
        label="Lease identifier", max_length=255, required=False, empty_value=None
    )
    tenant_name = forms.CharField(label="Tenant name", max_length=255, required=False)
    tenantcontact_type = CommaSeparatedChoiceField(
        label="Tenant role",
        required=False,
        choices=tuple((x.value, str(x)) for x in TenantContactType),
    )
    only_past_tenants = forms.BooleanField(label="Only past tenants", required=False)
    tenant_activity = forms.ChoiceField(
        label="Tenants",
        required=False,
        choices=(
            ("all", "All"),
            ("past", "Only past tenants"),
            ("active", "Only active tenants"),
        ),
    )
    lease_start_date_start = forms.DateField(required=False)
    lease_start_date_end = forms.DateField(required=False)
    lease_end_date_start = forms.DateField(required=False)
    lease_end_date_end = forms.DateField(required=False)
    only_active_leases = forms.BooleanField(label="Active", required=False)
    only_expired_leases = forms.BooleanField(label="Expired", required=False)
    has_geometry = forms.NullBooleanField(label="Has geometry", required=False)
    property_identifier = forms.CharField(
        label="Real property identifier",
        max_length=255,
        required=False,
        empty_value=None,
    )
    address = forms.CharField(
        label="Address", max_length=255, required=False, empty_value=None
    )
    lease_type = forms.ModelChoiceField(
        label="Lease type", queryset=LeaseType.objects.all(), required=False
    )
    municipality = forms.ModelChoiceField(
        label="Municipality", queryset=Municipality.objects.all(), required=False
    )
    district = forms.ModelChoiceField(
        label="District", queryset=District.objects.all(), required=False
    )
    sequence = forms.IntegerField(label="Sequence", required=False)
    lease_state = CommaSeparatedChoiceField(
        label="Lease state",
        required=False,
        choices=tuple((x.value, str(x)) for x in LeaseState),
    )
    business_id = forms.CharField(
        label="Business id",
        max_length=255,
        required=False,
        empty_value=None,
        validators=[validate_business_id],
    )
    national_identification_number = forms.CharField(
        label="National identification number",
        max_length=255,
        required=False,
        empty_value=None,
    )
    lessor = forms.ModelChoiceField(
        label="Lessor", queryset=Contact.objects.filter(is_lessor=True), required=False
    )
    contract_number = forms.CharField(
        label="Contract number", max_length=255, required=False, empty_value=None
    )
    decision_maker = forms.ModelChoiceField(
        label="Decision maker", queryset=DecisionMaker.objects.all(), required=False
    )
    decision_date = forms.DateField(required=False)
    decision_section = forms.CharField(
        label="Decision section", max_length=255, required=False, empty_value=None
    )
    reference_number = forms.CharField(
        label="Reference number", max_length=255, required=False, empty_value=None
    )
    invoice_number = forms.CharField(
        label="Invoice number", max_length=255, required=False, empty_value=None
    )


class BasisOfRentSearchForm(forms.Form):
    search = forms.CharField(
        label="Search", max_length=255, required=False, empty_value=None
    )
    decision_maker = forms.ModelChoiceField(
        label="Decision maker", queryset=DecisionMaker.objects.all(), required=False
    )
    decision_date = forms.DateField(required=False)
    decision_section = forms.CharField(
        label="Decision section", max_length=255, required=False, empty_value=None
    )
    reference_number = forms.CharField(
        label="Reference number", max_length=255, required=False, empty_value=None
    )


class InfillDevelopmentCompensationSearchForm(forms.Form):
    search = forms.CharField(
        label="Search", max_length=255, required=False, empty_value=None
    )
    state = CommaSeparatedChoiceField(
        label="State",
        required=False,
        choices=tuple((x.value, str(x)) for x in InfillDevelopmentCompensationState),
    )

    decision_maker = forms.ModelChoiceField(
        label="Decision maker", queryset=DecisionMaker.objects.all(), required=False
    )
    decision_date = forms.DateField(required=False)
    decision_section = forms.CharField(
        label="Decision section", max_length=255, required=False, empty_value=None
    )
    reference_number = forms.CharField(
        label="Reference number", max_length=255, required=False, empty_value=None
    )
