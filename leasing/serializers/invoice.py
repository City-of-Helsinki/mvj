from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.enums import InvoiceState
from leasing.models import Contact, Invoice
from leasing.models.invoice import InvoiceRow
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin

from .contact import ContactSerializer


class InvoiceRowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = InvoiceRow
        exclude = ('deleted',)


class InvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Invoice
        exclude = ('deleted',)


class InvoiceCreateSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)

    def create(self, validated_data):
        validated_data['state'] = InvoiceState.OPEN

        return super().create(validated_data)

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('sent_to_sap_at', 'sap_id', 'state', 'paid_amount', 'paid_date', 'outstanding_amount')


class InvoiceUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('sent_to_sap_at', 'sap_id', 'state', 'paid_amount', 'paid_date', 'outstanding_amount')
