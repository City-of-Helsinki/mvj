from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models.land_use_agreement import LandUseAgreement
from leasing.serializers.land_use_agreement import (
    LandUseAgreementCreateSerializer,
    LandUseAgreementListSerializer,
    LandUseAgreementRetrieveSerializer,
    LandUseAgreementUpdateSerializer,
)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class LandUseAgreementViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = LandUseAgreement.objects.all()
    serializer_class = LandUseAgreementRetrieveSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return LandUseAgreementCreateSerializer

        if self.action in ("update", "partial_update"):
            return LandUseAgreementUpdateSerializer

        if self.action == "list":
            return LandUseAgreementListSerializer

        return LandUseAgreementRetrieveSerializer
