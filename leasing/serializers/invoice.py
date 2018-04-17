from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import Invoice

from .contact import ContactSerializer


class InvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    recipient = ContactSerializer()

    class Meta:
        model = Invoice
        exclude = ('deleted',)
