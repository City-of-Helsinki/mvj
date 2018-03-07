from rest_framework import viewsets

from leasing.models import Contact
from leasing.serializers.contact import ContactSerializer


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
