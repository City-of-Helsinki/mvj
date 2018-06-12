from rest_framework import viewsets

from leasing.models import BasisOfRent
from leasing.serializers.basis_of_rent import BasisOfRentCreateUpdateSerializer, BasisOfRentSerializer
from leasing.viewsets.utils import AuditLogMixin


class BasisOfRentViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = BasisOfRent.objects.all()
    serializer_class = BasisOfRentSerializer

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return BasisOfRentCreateUpdateSerializer

        return BasisOfRentSerializer
