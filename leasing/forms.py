from django import forms

from leasing.enums import LeaseState, TenantContactType
from leasing.models import District, LeaseType, Municipality


class LeaseSearchForm(forms.Form):
    succinct = forms.BooleanField(label='Succinct', required=False)
    identifier = forms.CharField(label='Lease identifier', max_length=255, required=False, empty_value=None)
    tenant_name = forms.CharField(label='Tenant name', max_length=255, required=False)
    tenantcontact_type = forms.ChoiceField(label='Tenant role', required=False,
                                           choices=tuple((x.value, str(x)) for x in TenantContactType))
    only_past_tenants = forms.BooleanField(label='Only past tenants', required=False)  # TODO: spelling
    lease_start_date_start = forms.DateField(required=False)
    lease_start_date_end = forms.DateField(required=False)
    lease_end_date_start = forms.DateField(required=False)
    lease_end_date_end = forms.DateField(required=False)
    only_active_leases = forms.BooleanField(label='Active', required=False)
    only_expired_leases = forms.BooleanField(label='Expired', required=False)
    property_identifier = forms.CharField(label='Real property identifier', max_length=255, required=False,
                                          empty_value=None)
    address = forms.CharField(label='Address', max_length=255, required=False, empty_value=None)
    lease_type = forms.ModelChoiceField(label='Lease type', queryset=LeaseType.objects.all(), required=False)
    municipality = forms.ModelChoiceField(label='Municipality', queryset=Municipality.objects.all(), required=False)
    district = forms.ModelChoiceField(label='District', queryset=District.objects.all(), required=False)
    sequence = forms.IntegerField(label='Sequence', required=False)
    lease_state = forms.ChoiceField(label='Lease state', required=False,
                                    choices=tuple((x.value, str(x)) for x in LeaseState))
