from django_filters.rest_framework import FilterSet

from .models import Contact, Lease


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'is_business', 'business_name', 'business_id',
                  'national_identification_number', 'customer_number', 'sap_customer_number', 'partner_code',
                  'is_lessor']


class LeaseFilter(FilterSet):
    class Meta:
        model = Lease
        fields = ['type', 'municipality', 'district']
