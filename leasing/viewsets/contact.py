from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import CoalesceOrderingFilter, ContactFilter
from leasing.models import Contact
from leasing.serializers.contact import ContactCreateUpdateSerializer, ContactSerializer

from .utils import AtomicTransactionModelViewSet


class ContactViewSet(
    FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        CoalesceOrderingFilter,
    )
    search_fields = (
        "id",
        "first_name",
        "last_name",
        "name",
        "business_id",
        "sap_customer_number",
        "care_of",
    )
    ordering_fields = (
        "names",
        "first_name",
        "last_name",
        "name",
        "business_id",
        "type",
        "care_of",
    )
    coalesce_ordering = {"names": ("name", "last_name")}
    ordering = ("names", "first_name")

    def get_queryset(self):
        return Contact.objects.select_related("service_unit")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return ContactCreateUpdateSerializer

        return ContactSerializer
