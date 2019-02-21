from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import CoalesceOrderingFilter, ContactFilter
from leasing.models import Contact
from leasing.serializers.contact import ContactSerializer

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class ContactViewSet(AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, CoalesceOrderingFilter)
    search_fields = ('first_name', 'last_name', 'name', 'business_id', 'customer_number', 'sap_customer_number')
    ordering_fields = ('names', 'first_name', 'last_name', 'name', 'business_id', 'type')
    coalesce_ordering = {'names': ('name', 'last_name')}
    ordering = ('names', 'first_name')
