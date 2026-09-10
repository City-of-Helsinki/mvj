from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError

from field_permissions.serializers import FieldPermissionsSerializerMixin
from file_operations.serializers.mixins import FileSerializerMixin
from leasing.enums import CollectionStage
from leasing.models import Invoice, Lease, Tenant
from users.serializers import UserSerializer

from ..models.debt_collection import (
    CollectionCourtDecision,
    CollectionLetter,
    CollectionLetterTemplate,
    CollectionNote,
)
from .utils import InstanceDictPrimaryKeyRelatedField


class CollectionCourtDecisionSerializer(
    FileSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = CollectionCourtDecision
        fields = (
            "id",
            "lease",
            "file",
            "decision_date",
            "note",
            "filename",
            "uploader",
            "uploaded_at",
        )
        download_url_name = "collectioncourtdecision-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class CollectionCourtDecisionCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionCourtDecision
        fields = (
            "id",
            "lease",
            "file",
            "decision_date",
            "note",
            "uploader",
            "uploaded_at",
        )
        read_only_fields = ("uploaded_at",)

    def validate(self, data):
        request = self.context.get("request")
        if (
            data.get("lease").service_unit not in request.user.service_units.all()
            and not request.user.is_superuser
        ):
            raise ValidationError(
                _(
                    "Can not add a court decision for an invoice belonging to another service unit"
                )
            )
        return data


class CollectionLetterSerializer(
    FileSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = CollectionLetter
        fields = ("id", "lease", "file", "filename", "uploader", "uploaded_at")
        download_url_name = "collectionletter-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class CollectionLetterCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionLetter
        fields = ("id", "lease", "file", "uploader", "uploaded_at")
        read_only_fields = ("uploaded_at",)

    def validate(self, data):
        request = self.context.get("request")
        if (
            data.get("lease").service_unit not in request.user.service_units.all()
            and not request.user.is_superuser
        ):
            raise PermissionDenied(
                _(
                    "Can not add a collection letter for an invoice belonging to another service unit"
                )
            )
        return data


class CollectionLetterTemplateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = CollectionLetterTemplate
        fields = ("id", "name")


class CollectionNoteSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    user = UserSerializer(read_only=True)

    class Meta:
        model = CollectionNote
        fields = "__all__"


class CollectionNoteCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CollectionNote
        fields = "__all__"

    def create(self, validated_data):
        collection_note: CollectionNote = super().create(validated_data)

        if (
            collection_note.collection_stage == CollectionStage.PAYMENT_DEFERRAL
            and collection_note.postpone_date
        ):
            invoice: Invoice = collection_note.invoices.first()
            invoice.postpone_date = collection_note.postpone_date
            invoice.save()

        return collection_note

    def validate(self, data):
        self._validate_service_unit(data)

        collection_stage = data.get("collection_stage")
        invoices = data.get("invoices")

        # If collection stage does not exist, do not validate conditional fields.
        # Can happen when editing old collection notes that were created before the collection stage field was added.
        if not collection_stage:
            return data

        self._validate_invoices(collection_stage, invoices)
        self._validate_payment_deferral(collection_stage, data, invoices)
        self._validate_contract_change(collection_stage, data)

        return data

    def _validate_service_unit(self, data):
        request = self.context.get("request")
        lease = data.get("lease") or (self.instance and self.instance.lease)
        if (
            lease.service_unit not in request.user.service_units.all()
            and not request.user.is_superuser
        ):
            raise ValidationError(
                _(
                    "Can not create a collection note for an invoice belonging to another service unit"
                )
            )

    def _validate_invoices(self, collection_stage, invoices):
        # Invoices are required for all types except for a simple NOTICE.
        if collection_stage != CollectionStage.NOTICE and not invoices:
            raise ValidationError(
                _("Invoices must be provided for this type of collection note")
            )

    def _validate_payment_deferral(self, collection_stage, data, invoices):
        postpone_date = data.get("postpone_date")
        if collection_stage == CollectionStage.PAYMENT_DEFERRAL:
            # Payment deferrals accept only one invoice.
            if invoices and len(invoices) != 1:
                raise ValidationError(
                    _("Payment deferrals must be targeted to a single invoice")
                )
            if not postpone_date:
                raise ValidationError(_("Missing postpone date for payment deferral"))
        elif postpone_date:
            raise ValidationError(
                _("Postpone date can only be set for payment deferrals")
            )

    def _validate_contract_change(self, collection_stage, data):
        if collection_stage != CollectionStage.CONTRACT_CHANGE:
            if data.get("entire_lease"):
                raise ValidationError(
                    _("'Entire lease' can only be set for contract changes")
                )
            if data.get("inspection_date"):
                raise ValidationError(
                    _("Inspection date can only be set for contract changes")
                )


class CreateCollectionLetterDocumentInvoiceSerializer(serializers.Serializer):
    invoice = serializers.PrimaryKeyRelatedField(queryset=Invoice.objects.all())
    collection_charge = serializers.DecimalField(max_digits=12, decimal_places=2)


class CreateCollectionLetterDocumentSerializer(serializers.Serializer):
    lease = InstanceDictPrimaryKeyRelatedField(
        instance_class=Lease, queryset=Lease.objects.all()
    )
    template = InstanceDictPrimaryKeyRelatedField(
        instance_class=CollectionLetterTemplate,
        queryset=CollectionLetterTemplate.objects.all(),
    )
    tenants = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tenant.objects.all()
    )
    invoices = CreateCollectionLetterDocumentInvoiceSerializer(many=True)

    # TODO: Validate tenant and invoices
