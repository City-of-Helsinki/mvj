from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from ..models import LeaseholdTransfer
from ..serializers.leasehold_transfer import LeaseholdTransferSerializer


class LeaseholdTransferViewSet(ReadOnlyModelViewSet):
    queryset = LeaseholdTransfer.objects.all()
    serializer_class = LeaseholdTransferSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = (
        'properties__identifier', 'decision_date', 'institution_identifier',
        'parties__name')
    ordering_fields = ('decision_date', 'institution_identifier')
    ordering = ('-decision_date',)
