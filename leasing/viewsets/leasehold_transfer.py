from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from field_permissions.viewsets import FieldPermissionsViewsetMixin

from ..models import LeaseholdTransfer
from ..serializers.leasehold_transfer import LeaseholdTransferSerializer


class LeaseholdTransferViewSet(FieldPermissionsViewsetMixin, RetrieveModelMixin, ListModelMixin, DestroyModelMixin,
                               GenericViewSet):
    queryset = LeaseholdTransfer.objects.all()
    serializer_class = LeaseholdTransferSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    search_fields = ('properties__identifier', 'decision_date', 'institution_identifier', 'parties__name')
    ordering_fields = ('decision_date', 'institution_identifier')
    ordering = ('-decision_date',)

    def get_queryset(self):
        if self.request.query_params.get('with_deleted'):
            return LeaseholdTransfer.objects.all_with_deleted()

        return LeaseholdTransfer.objects.all()
