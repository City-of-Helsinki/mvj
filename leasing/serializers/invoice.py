from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.enums import InvoiceState
from leasing.models import Contact, Invoice, Tenant
from leasing.models.invoice import InvoiceRow, ReceivableType
from leasing.serializers.tenant import TenantSerializer
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin

from .contact import ContactSerializer


class ReceivableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceivableType
        fields = '__all__'


class InvoiceRowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tenant = TenantSerializer()

    class Meta:
        model = InvoiceRow
        fields = ('id', 'tenant', 'receivable_type', 'billing_period_start_date', 'billing_period_end_date',
                  'description', 'amount')


class InvoiceRowCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    tenant = InstanceDictPrimaryKeyRelatedField(instance_class=Tenant,
                                                queryset=Tenant.objects.all(),
                                                related_serializer=TenantSerializer)
    receivable_type = InstanceDictPrimaryKeyRelatedField(instance_class=ReceivableType,
                                                         queryset=ReceivableType.objects.all(),
                                                         related_serializer=ReceivableTypeSerializer)

    class Meta:
        model = InvoiceRow
        fields = ('id', 'tenant', 'receivable_type', 'billing_period_start_date', 'billing_period_end_date',
                  'description', 'amount')


class InvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Invoice
        exclude = ('deleted',)


class InvoiceCreateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)
    rows = InvoiceRowCreateUpdateSerializer(many=True)

    def create(self, validated_data):
        validated_data['state'] = InvoiceState.OPEN

        return super().create(validated_data)

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('generated', 'sent_to_sap_at', 'sap_id', 'state')


class InvoiceUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)
    rows = InvoiceRowCreateUpdateSerializer(many=True)

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('generated', 'sent_to_sap_at', 'sap_id', 'state')
