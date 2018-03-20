from django_filters.rest_framework import FilterSet

from .models import Comment, Contact, Lease


class CommentFilter(FilterSet):
    class Meta:
        model = Comment
        fields = ['lease', 'user', 'topic', 'is_archived']


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
