from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from field_permissions.serializers import FieldPermissionsSerializerMixin
from file_operations.serializers.mixins import FileSerializerMixin
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
            raise ValidationError(  # TODO this needs to be a permissiondenied
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

    def validate(self, data):
        request = self.context.get("request")
        if (
            data.get("lease").service_unit not in request.user.service_units.all()
            and not request.user.is_superuser
        ):
            raise ValidationError(
                _(
                    "Can not create a collection note for an invoice belonging to another service unit"
                )
            )
        return data


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
