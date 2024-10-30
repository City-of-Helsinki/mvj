import datetime
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from random import choice

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Contact, Tenant
from leasing.models.invoice import (
    Invoice,
    InvoiceNote,
    InvoicePayment,
    InvoiceRow,
    InvoiceSet,
)
from leasing.models.receivable_type import ReceivableType
from leasing.models.utils import fix_amount_for_overlap, subtract_ranges_from_ranges
from leasing.serializers.explanation import ExplanationSerializer
from leasing.serializers.receivable_type import ReceivableTypeSerializer
from leasing.serializers.tenant import TenantSerializer
from leasing.serializers.utils import (
    InstanceDictPrimaryKeyRelatedField,
    UpdateNestedMixin,
)

from .contact import ContactSerializer
from .service_unit import ServiceUnitSerializer


class InvoiceNoteSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        # Lease field must be added dynamically to prevent circular imports
        from leasing.serializers.lease import LeaseSuccinctSerializer

        self.fields["lease"] = LeaseSuccinctSerializer()

    class Meta:
        model = InvoiceNote
        exclude = ("deleted",)


class InvoiceNoteCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        # Lease field must be added dynamically to prevent circular imports
        from leasing.models.lease import Lease
        from leasing.serializers.lease import LeaseSuccinctSerializer

        self.fields["lease"] = InstanceDictPrimaryKeyRelatedField(
            instance_class=Lease,
            queryset=Lease.objects.all(),
            related_serializer=LeaseSuccinctSerializer,
        )

    class Meta:
        model = InvoiceNote
        exclude = ("deleted",)


class InvoicePaymentSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = InvoicePayment
        exclude = ("deleted",)


class InvoicePaymentCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = InvoicePayment
        exclude = ("invoice", "deleted")


class InvoiceRowSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    tenant = TenantSerializer()

    class Meta:
        model = InvoiceRow
        fields = (
            "id",
            "tenant",
            "receivable_type",
            "billing_period_start_date",
            "billing_period_end_date",
            "description",
            "amount",
        )


class InvoiceRowCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    tenant = InstanceDictPrimaryKeyRelatedField(
        instance_class=Tenant,
        queryset=Tenant.objects.all(),
        related_serializer=TenantSerializer,
        required=False,
        allow_null=True,
    )
    receivable_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=ReceivableType,
        queryset=ReceivableType.objects.all(),
        related_serializer=ReceivableTypeSerializer,
    )

    class Meta:
        model = InvoiceRow
        fields = (
            "id",
            "tenant",
            "receivable_type",
            "billing_period_start_date",
            "billing_period_end_date",
            "description",
            "amount",
        )

    def validate(self, data):
        """Validate that rows with an inactive receivable type cannot be created

        Saving an existing row should succeed, but creating
        new rows or changing a rows receivable type to an inactive type
        should fail."""

        valid = True

        if not data["receivable_type"].is_active:
            if self.instance:
                if self.instance.receivable_type != data["receivable_type"]:
                    # We have an existing row but the receivable type wasn't the
                    # same as before
                    valid = False
            else:
                # We have data without an instance.
                # If there is no id it's a new row.
                if "id" not in data:
                    valid = False
                else:
                    # Else try to see if the existing row has the same receivable type
                    try:
                        existing_row = InvoiceRow.objects.get(pk=data["id"])

                        if existing_row.receivable_type != data["receivable_type"]:
                            valid = False
                    except ObjectDoesNotExist:
                        valid = False

        if not valid:
            raise ValidationError(_("Cannot use an inactive receivable type"))

        request = self.context.get("request")

        if data["receivable_type"].service_unit not in request.user.service_units.all():
            raise ValidationError(
                _(
                    "Can only use receivable types from service units the user is a member of"
                )
            )

        return data


class InlineInvoiceSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = Invoice
        fields = ("id", "number", "due_date", "total_amount")


class InvoiceSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)
    payments = InvoicePaymentSerializer(many=True, required=False, allow_null=True)
    credit_invoices = InlineInvoiceSerializer(
        many=True, required=False, allow_null=True
    )
    interest_invoices = InlineInvoiceSerializer(
        many=True, required=False, allow_null=True
    )
    service_unit = ServiceUnitSerializer(read_only=True)

    class Meta:
        model = Invoice
        exclude = ("deleted",)


class InvoiceSerializerWithSuccinctLease(InvoiceSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        # Lease field must be added dynamically to prevent circular imports
        from leasing.serializers.lease import LeaseSuccinctSerializer

        self.fields["lease"] = LeaseSuccinctSerializer()


class InvoiceSerializerWithExplanations(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    recipient = ContactSerializer()
    rows = InvoiceRowSerializer(many=True, required=False, allow_null=True)
    payments = InvoicePaymentSerializer(many=True, required=False, allow_null=True)
    explanations = serializers.ListField(child=ExplanationSerializer(read_only=True))

    class Meta:
        model = Invoice
        exclude = ("deleted",)


class InvoiceCreateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
        required=False,
    )
    tenant = InstanceDictPrimaryKeyRelatedField(
        instance_class=Tenant,
        queryset=Tenant.objects.all(),
        related_serializer=TenantSerializer,
        required=False,
    )
    rows = InvoiceRowCreateUpdateSerializer(many=True)
    payments = InvoicePaymentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    # Make total_amount, billed_amount, and type not required in the serializer and set them in create() if needed
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    billed_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    type = EnumField(enum=InvoiceType, required=False)
    service_unit = ServiceUnitSerializer(read_only=True)

    def override_permission_check_field_name(self, field_name):
        if field_name == "tenant":
            return "recipient"

        return field_name

    def validate(self, attrs):
        request = self.context.get("request")
        if (
            attrs.get("lease").service_unit not in request.user.service_units.all()
            and not request.user.is_superuser
        ):
            raise ValidationError(
                _("Can only add invoices to service units the user is a member of")
            )

        if not bool(attrs.get("recipient")) ^ bool(attrs.get("tenant")):
            raise ValidationError(_("Either recipient or tenant is required."))

        if (
            attrs.get("tenant")
            and attrs.get("tenant") not in attrs.get("lease").tenants.all()
        ):
            raise ValidationError(_("Tenant not found in lease"))

        return attrs

    def create(self, validated_data):
        validated_data["state"] = InvoiceState.OPEN
        validated_data["service_unit"] = validated_data["lease"].service_unit

        if not validated_data.get("total_amount"):
            total_amount = Decimal(0)
            for row in validated_data.get("rows", []):
                total_amount += row.get("amount", Decimal(0))

            validated_data["total_amount"] = total_amount

        if not validated_data.get("billed_amount"):
            billed_amount = Decimal(0)
            for row in validated_data.get("rows", []):
                billed_amount += row.get("amount", Decimal(0))

            validated_data["billed_amount"] = billed_amount

        if not validated_data.get("type"):
            validated_data["type"] = InvoiceType.CHARGE

        if validated_data.get("tenant"):
            today = datetime.date.today()
            tenant = validated_data.pop("tenant")
            billing_tenantcontact = tenant.get_billing_tenantcontacts(
                start_date=today, end_date=None
            ).first()
            if not billing_tenantcontact:
                raise ValidationError(_("Billing contact not found for tenant"))

            validated_data["recipient"] = billing_tenantcontact.contact
            for row in validated_data.get("rows", []):
                row["tenant"] = tenant

        invoice = super().create(validated_data)

        invoice.invoicing_date = timezone.now().date()
        invoice.outstanding_amount = validated_data["total_amount"]
        invoice.update_amounts()  # 0€ invoice would stay OPEN otherwise
        invoice.save()

        return invoice

    class Meta:
        model = Invoice
        exclude = ("deleted",)
        read_only_fields = (
            "number",
            "generated",
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "credit_invoices",
            "interest_invoices",
        )


class InvoiceUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
    )
    rows = InvoiceRowCreateUpdateSerializer(many=True)
    payments = InvoicePaymentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.update_amounts()
        if instance.credited_invoice:
            instance.credited_invoice.update_amounts()

        return instance

    class Meta:
        model = Invoice
        exclude = ("deleted",)
        read_only_fields = (
            "generated",
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "credit_invoices",
            "interest_invoices",
        )


class CreditNoteUpdateSerializer(InvoiceUpdateSerializer):
    class Meta:
        model = Invoice
        exclude = ("deleted",)
        read_only_fields = (
            "generated",
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "due_date",
            "billing_period_start_date",
            "billing_period_end_date",
        )


class GeneratedInvoiceUpdateSerializer(InvoiceUpdateSerializer):
    """Invoice serializer where all but "payments" is read only"""

    rows = InvoiceRowCreateUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        exclude = ("deleted",)
        read_only_fields = (
            "lease",
            "invoiceset",
            "number",
            "recipient",
            "sent_to_sap_at",
            "sap_id",
            "adjusted_due_date",
            "due_date",
            "invoicing_date",
            "state",
            "billing_period_start_date",
            "billing_period_end_date",
            "total_amount",
            "billed_amount",
            "outstanding_amount",
            "payment_notification_date",
            "collection_charge",
            "payment_notification_catalog_date",
            "delivery_method",
            "type",
            "notes",
            "generated",
            "description",
            "credited_invoices",
            "interest_invoices",
            "rows",
        )


class SentToSapInvoiceUpdateSerializer(InvoiceUpdateSerializer):
    """Invoice serializer where all but "postpone_date" is read only"""

    rows = InvoiceRowCreateUpdateSerializer(many=True, read_only=True)
    payments = InvoicePaymentCreateUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        exclude = ("deleted",)
        read_only_fields = (
            "lease",
            "invoiceset",
            "number",
            "recipient",
            "sent_to_sap_at",
            "sap_id",
            "adjusted_due_date",
            "due_date",
            "invoicing_date",
            "state",
            "billing_period_start_date",
            "billing_period_end_date",
            "total_amount",
            "billed_amount",
            "outstanding_amount",
            "payment_notification_date",
            "collection_charge",
            "payment_notification_catalog_date",
            "delivery_method",
            "type",
            "notes",
            "generated",
            "description",
            "credited_invoices",
            "interest_invoices",
            "rows",
            "payments",
        )


class InvoiceSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceSet
        fields = (
            "id",
            "lease",
            "billing_period_start_date",
            "billing_period_end_date",
            "invoices",
        )


class CreateChargeInvoiceRowSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    receivable_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=ReceivableType,
        queryset=ReceivableType.objects.all(),
        related_serializer=ReceivableTypeSerializer,
    )


class CreateChargeSerializer(serializers.Serializer):
    due_date = serializers.DateField()
    billing_period_start_date = serializers.DateField(required=False)
    billing_period_end_date = serializers.DateField(required=False)
    rows = serializers.ListSerializer(
        child=CreateChargeInvoiceRowSerializer(), required=True
    )
    notes = serializers.CharField(required=False)

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        # Lease field must be added dynamically to prevent circular imports
        from leasing.models.lease import Lease
        from leasing.serializers.lease import LeaseSuccinctSerializer

        self.fields["lease"] = InstanceDictPrimaryKeyRelatedField(
            instance_class=Lease,
            queryset=Lease.objects.all(),
            related_serializer=LeaseSuccinctSerializer,
        )

    def to_representation(self, instance):
        if isinstance(instance, InvoiceSet):
            return InvoiceSetSerializer().to_representation(instance=instance)
        elif isinstance(instance, Invoice):
            return InvoiceSerializer().to_representation(instance=instance)

    def validate(self, data):
        if (
            data.get("billing_period_start_date")
            and not data.get("billing_period_end_date")
        ) or (
            not data.get("billing_period_start_date")
            and data.get("billing_period_end_date")
        ):
            raise serializers.ValidationError(
                _(
                    "Both Billing period start and end are "
                    "required if one of them is provided"
                )
            )

        if data.get("billing_period_start_date", 0) > data.get(
            "billing_period_end_date", 0
        ):
            raise serializers.ValidationError(
                _("Billing period end must be the same or after the start")
            )

        return data

    def create(self, validated_data):  # noqa: C901 TODO
        today = timezone.now().date()
        lease = validated_data.get("lease")
        billing_period_start_date = validated_data.get(
            "billing_period_start_date", today
        )
        billing_period_end_date = validated_data.get("billing_period_end_date", today)
        billing_period = (billing_period_start_date, billing_period_end_date)

        total_amount = sum(
            [row.get("amount") for row in validated_data.get("rows", [])]
        )

        # TODO: Handle possible exception
        shares = lease.get_tenant_shares_for_period(
            billing_period_start_date, billing_period_end_date
        )

        invoice = None
        invoiceset = None

        if len(shares.items()) > 1:
            invoiceset = InvoiceSet.objects.create(
                lease=lease,
                billing_period_start_date=billing_period_start_date,
                billing_period_end_date=billing_period_end_date,
            )

        invoice_data = []

        # TODO: check for periods without 1/1 shares
        for contact, share in shares.items():
            invoice_rows_by_index = defaultdict(list)

            for tenant, overlaps in share.items():
                for row_index, row in enumerate(validated_data.get("rows", [])):
                    overlap_amount = Decimal(0)
                    for overlap in overlaps:
                        overlap_amount += fix_amount_for_overlap(
                            row.get("amount", Decimal(0)),
                            overlap,
                            subtract_ranges_from_ranges([billing_period], [overlap]),
                        )

                        # Notice! Custom charge uses tenant share, not rent share
                        share_amount = Decimal(
                            overlap_amount
                            * Decimal(tenant.share_numerator / tenant.share_denominator)
                        ).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)

                        invoice_rows_by_index[row_index].append(
                            {
                                "tenant": tenant,
                                "receivable_type": row.get("receivable_type"),
                                "billing_period_start_date": overlap[0],
                                "billing_period_end_date": overlap[1],
                                "amount": share_amount,
                            }
                        )

            invoice_data.append(
                {
                    "type": InvoiceType.CHARGE,
                    "lease": lease,
                    "service_unit": lease.service_unit,
                    "recipient": contact,
                    "due_date": validated_data.get("due_date"),
                    "invoicing_date": today,
                    "state": InvoiceState.OPEN,
                    "billing_period_start_date": billing_period_start_date,
                    "billing_period_end_date": billing_period_end_date,
                    "total_amount": total_amount,
                    "invoiceset": invoiceset,
                    "notes": validated_data.get("notes", ""),
                    "rows": invoice_rows_by_index,
                }
            )

        # Check that the total row amount is correct or add the missing
        # amount to a random invoice if not
        for input_row_index, input_row in enumerate(validated_data.get("rows", [])):
            row_sum = Decimal(0)
            all_rows = []
            for invoice_datum in invoice_data:
                for row_data in invoice_datum["rows"][input_row_index]:
                    row_sum += row_data["amount"]
                    all_rows.append(row_data)

            difference = input_row["amount"] - row_sum
            if difference:
                random_row = choice(all_rows)
                random_row["amount"] += difference

        # Flatten rows, update totals and save the invoices
        for invoice_datum in invoice_data:
            invoice_datum["rows"] = [
                row for rows in invoice_datum["rows"].values() for row in rows
            ]
            rows_sum = sum([row["amount"] for row in invoice_datum["rows"]])
            invoice_datum["billed_amount"] = rows_sum
            invoice_datum["outstanding_amount"] = rows_sum

            invoice_row_data = invoice_datum.pop("rows")

            invoice = Invoice.objects.create(**invoice_datum)

            for invoice_row_datum in invoice_row_data:
                invoice_row_datum["invoice"] = invoice
                InvoiceRow.objects.create(**invoice_row_datum)

        if invoiceset:
            return invoiceset
        else:
            return invoice
