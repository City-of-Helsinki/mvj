from django import forms


# TODO: validation
class LeaseSearchForm(forms.Form):
    succinct = forms.BooleanField(label='Succinct', required=False)
    identifier = forms.CharField(label='Lease identifier', max_length=255, required=False, empty_value=None)
    tenant = forms.CharField(label='Tenant name', max_length=255, required=False)
    # TODO: choices
    tenant_role = forms.CharField(label='Tenant role', max_length=255, required=False, empty_value=None)
    only_past_tentants = forms.BooleanField(label='Only past tenants', required=False)  # TODO: spelling
    lease_start_date_start = forms.DateField(required=False)
    lease_start_date_end = forms.DateField(required=False)
    lease_end_date_start = forms.DateField(required=False)
    lease_end_date_end = forms.DateField(required=False)
    on_going = forms.BooleanField(label='Active', required=False)
    expired = forms.BooleanField(label='Expired', required=False)
    property_identifier = forms.CharField(label='Real property identifier', max_length=255, required=False,
                                          empty_value=None)
    address = forms.CharField(label='Address', max_length=255, required=False, empty_value=None)
    type = forms.IntegerField(label='Lease type', required=False)  # TODO: choices
    municipality = forms.IntegerField(label='Municipality', required=False)  # TODO: choices
    district = forms.IntegerField(label='District', required=False)  # TODO: choices
    sequence = forms.IntegerField(label='Sequence', required=False)
    state = forms.CharField(label='Lease state', max_length=255, required=False, empty_value=None)  # TODO: choices
