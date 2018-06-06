from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from leasing.filters import ContactFilter
from leasing.models import Contact
from leasing.serializers.contact import ContactSerializer
from leasing.viewsets.utils import AuditLogMixin


class ContactViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_class = ContactFilter
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    search_fields = ('first_name', 'last_name', 'name', 'business_id', 'customer_number', 'sap_customer_number')
