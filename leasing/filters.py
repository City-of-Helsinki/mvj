from django_filters.rest_framework import FilterSet

from leasing.models.lease import Lease


class LeaseFilter(FilterSet):
    class Meta:
        model = Lease
        fields = ['type', 'municipality', 'district', 'sequence']
