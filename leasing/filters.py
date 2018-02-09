from django_filters.rest_framework import FilterSet

from leasing.models import Asset, Client, Lease


class ClientFilter(FilterSet):
    class Meta:
        model = Client
        fields = ['legacy_id']


class LeaseFilter(FilterSet):
    class Meta:
        model = Lease
        fields = ['type', 'municipality', 'district', 'sequence', 'status']


class AssetFilter(FilterSet):
    class Meta:
        model = Asset
        fields = ['type', 'address', 'surface_area']
