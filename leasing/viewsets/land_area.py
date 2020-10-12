from rest_framework import filters, mixins
from rest_framework.viewsets import GenericViewSet

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.models import LeaseAreaAttachment
from leasing.models.land_area import PlanUnit
from leasing.serializers.land_area import (
    LeaseAreaAttachmentCreateUpdateSerializer,
    LeaseAreaAttachmentSerializer,
    PlanUnitListWithIdentifiersSerializer,
    PlanUnitSerializer,
)

from .utils import (
    AtomicTransactionModelViewSet,
    AuditLogMixin,
    FileMixin,
    MultiPartJsonParser,
)


class LeaseAreaAttachmentViewSet(
    FileMixin,
    AuditLogMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = LeaseAreaAttachment.objects.all()
    serializer_class = LeaseAreaAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return LeaseAreaAttachmentCreateUpdateSerializer

        return LeaseAreaAttachmentSerializer


class PlanUnitViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = PlanUnit.objects.all()
    serializer_class = PlanUnitSerializer


class PlanUnitListWithIdentifiersViewSet(mixins.ListModelMixin, GenericViewSet):
    search_fields = [
        "^lease_area__lease__identifier__identifier",
        "^lease_area__identifier",
        "^identifier",
    ]
    filter_backends = (filters.SearchFilter,)
    queryset = PlanUnit.objects.all()
    serializer_class = PlanUnitListWithIdentifiersSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_master=True)
            .select_related("lease_area")
            .only(
                "id",
                "identifier",
                "plan_unit_status",
                "lease_area__identifier",
                "lease_area__lease__identifier__identifier",
            )
        )
