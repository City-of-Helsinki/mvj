from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Contact, Invoice, Lease, Tenant
from leasing.models.invoice import InvoicePayment, InvoiceRow, InvoiceSet, ReceivableType
from leasing.models.utils import fix_amount_for_overlap, subtract_ranges_from_ranges
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.lease import LeaseSuccinctSerializer
from leasing.serializers.tenant import TenantSerializer
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin

from .contact import ContactSerializer


class ReceivableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceivableType
        fields = '__all__'


class InvoicePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        exclude = ('deleted',)


class InvoicePaymentCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = InvoicePayment
        exclude = ('invoice', 'deleted',)


class InvoiceRowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenant = TenantSerializer()

    class Meta:
        model = InvoiceRow
        fields = ('id', 'tenant', 'receivable_type', 'billing_period_start_date', 'billing_period_end_date',
                  'description', 'amount')


class InvoiceRowCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    tenant = InstanceDictPrimaryKeyRelatedField(instance_class=Tenant,
                                                queryset=Tenant.objects.all(),
                                                related_serializer=TenantSerializer, required=False, allow_null=True)
    receivable_type = InstanceDictPrimaryKeyRelatedField(instance_class=ReceivableType,
                                                         queryset=ReceivableType.objects.all(),
                                                         related_serializer=ReceivableTypeSerializer)

    class Meta:
        model = InvoiceRow
        fields = ('id', 'tenant', 'receivable_type', 'billing_period_start_date', 'billing_period_end_date',
                  'description', 'amount')


class CreditInvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id', 'number', 'due_date', 'total_amount')


class InvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)
    payments = InvoicePaymentSerializer(many=True, required=False, allow_null=True)
    credit_invoices = CreditInvoiceSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Invoice
        exclude = ('deleted',)


class InvoiceSerializerWithExplanations(EnumSupportSerializerMixin, serializers.ModelSerializer):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)
    payments = InvoicePaymentSerializer(many=True, required=False, allow_null=True)
    explanations = serializers.ListField(child=ExplanationSerializer(read_only=True))

    class Meta:
        model = Invoice
        exclude = ('deleted',)


class InvoiceCreateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)
    rows = InvoiceRowCreateUpdateSerializer(many=True)
    payments = InvoicePaymentCreateUpdateSerializer(many=True, required=False, allow_null=True)
    # Make total_amount, billed_amount, and type not requided in serializer and set them in create() if needed
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    billed_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    type = EnumField(enum=InvoiceType, required=False)

    def create(self, validated_data):
        validated_data['state'] = InvoiceState.OPEN

        if not validated_data.get('total_amount'):
            total_amount = Decimal(0)
            for row in validated_data.get('rows', []):
                total_amount += row.get('amount', Decimal(0))

            validated_data['total_amount'] = total_amount

        if not validated_data.get('billed_amount'):
            billed_amount = Decimal(0)
            for row in validated_data.get('rows', []):
                billed_amount += row.get('amount', Decimal(0))

            validated_data['billed_amount'] = billed_amount

        if not validated_data.get('type'):
            validated_data['type'] = InvoiceType.CHARGE

        return super().create(validated_data)

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('number', 'generated', 'sent_to_sap_at', 'sap_id', 'state', 'adjusted_due_date')


class InvoiceUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                   related_serializer=ContactSerializer)
    rows = InvoiceRowCreateUpdateSerializer(many=True)
    payments = InvoicePaymentCreateUpdateSerializer(many=True, required=False, allow_null=True)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.update_amounts()

        return instance

    class Meta:
        model = Invoice
        exclude = ('deleted',)
        read_only_fields = ('generated', 'sent_to_sap_at', 'sap_id', 'state', 'adjusted_due_date')


class InvoiceSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceSet
        fields = ('id', 'lease', 'billing_period_start_date', 'billing_period_end_date', 'invoices')


class CreateChargeInvoiceRowSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    receivable_type = InstanceDictPrimaryKeyRelatedField(instance_class=ReceivableType,
                                                         queryset=ReceivableType.objects.all(),
                                                         related_serializer=ReceivableTypeSerializer)


class CreateChargeSerializer(serializers.Serializer):
    lease = InstanceDictPrimaryKeyRelatedField(instance_class=Lease, queryset=Lease.objects.all(),
                                               related_serializer=LeaseSuccinctSerializer)
    due_date = serializers.DateField()
    billing_period_start_date = serializers.DateField(required=False)
    billing_period_end_date = serializers.DateField(required=False)
    rows = serializers.ListSerializer(child=CreateChargeInvoiceRowSerializer(), required=True)
    notes = serializers.CharField(required=False)

    def to_representation(self, instance):
        if isinstance(instance, InvoiceSet):
            return InvoiceSetSerializer().to_representation(instance=instance)
        elif isinstance(instance, Invoice):
            return InvoiceSerializer().to_representation(instance=instance)

    def validate(self, data):
        if (data.get('billing_period_start_date') and not data.get('billing_period_end_date')) or (
                not data.get('billing_period_start_date') and data.get('billing_period_end_date')):
            raise serializers.ValidationError(_("Both Billing period start and end are "
                                                "required if one of them is provided"))

        if data.get('billing_period_start_date') > data.get('billing_period_end_date'):
            raise serializers.ValidationError(_("Billing period end must be the same or after the start"))

        return data

    def create(self, validated_data):
        today = timezone.now().date()
        lease = validated_data.get('lease')
        billing_period_start_date = validated_data.get('billing_period_start_date', today)
        billing_period_end_date = validated_data.get('billing_period_end_date', today)
        billing_period = (billing_period_start_date, billing_period_end_date)

        total_amount = sum([row.get('amount') for row in validated_data.get('rows', [])])

        # TODO: Handle possible exception
        shares = lease.get_tenant_shares_for_period(billing_period_start_date, billing_period_end_date)

        invoice = None
        invoiceset = None

        if len(shares.items()) > 1:
            invoiceset = InvoiceSet.objects.create(lease=lease, billing_period_start_date=billing_period_start_date,
                                                   billing_period_end_date=billing_period_end_date)

        # TODO: check for periods without 1/1 shares
        for contact, share in shares.items():
            invoice_row_data = []
            billable_amount = Decimal(0)

            for tenant, overlaps in share.items():
                for row in validated_data.get('rows', []):
                    overlap_amount = Decimal(0)
                    for overlap in overlaps:
                        overlap_amount += fix_amount_for_overlap(
                            row.get('amount', Decimal(0)), overlap, subtract_ranges_from_ranges([billing_period],
                                                                                                [overlap]))

                        share_amount = Decimal(
                            overlap_amount * Decimal(tenant.share_numerator / tenant.share_denominator)
                        ).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

                        billable_amount += share_amount

                        invoice_row_data.append({
                            'tenant': tenant,
                            'receivable_type': row.get('receivable_type'),
                            'billing_period_start_date': overlap[0],
                            'billing_period_end_date': overlap[1],
                            'amount': share_amount,
                        })

            invoice = Invoice.objects.create(
                type=InvoiceType.CHARGE,
                lease=lease,
                recipient=contact,
                due_date=validated_data.get('due_date'),
                invoicing_date=today,
                state=InvoiceState.OPEN,
                billing_period_start_date=billing_period_start_date,
                billing_period_end_date=billing_period_end_date,
                total_amount=total_amount,
                billed_amount=billable_amount,
                outstanding_amount=billable_amount,
                invoiceset=invoiceset,
                notes=validated_data.get('notes', ''),
            )

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum['invoice'] = invoice
                InvoiceRow.objects.create(**invoice_row_datum)

        if invoiceset:
            return invoiceset
        else:
            return invoice
