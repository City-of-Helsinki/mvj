from rest_framework import viewsets

from leasing.filters import ContactFilter
from leasing.models import Contact
from leasing.serializers.contact import ContactSerializer
from leasing.viewsets.utils import AuditLogMixin


class ContactViewSet(AuditLogMixin, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_class = ContactFilter
