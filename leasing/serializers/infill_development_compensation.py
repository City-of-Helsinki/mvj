from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from file_operations.serializers.mixins import FileSerializerMixin
from leasing.models import DecisionMaker, IntendedUse, Lease
from users.models import User
from users.serializers import UserSerializer

from ..models import (
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationAttachment,
    InfillDevelopmentCompensationDecision,
    InfillDevelopmentCompensationIntendedUse,
    InfillDevelopmentCompensationLease,
)
from .decision import DecisionMakerSerializer
from .lease import IntendedUseSerializer, LeaseSuccinctSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class InfillDevelopmentCompensationDecisionSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    decision_maker = DecisionMakerSerializer()

    class Meta:
        model = InfillDevelopmentCompensationDecision
        fields = (
            "id",
            "reference_number",
            "decision_maker",
            "decision_date",
            "section",
        )


class InfillDevelopmentCompensationDecisionCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    decision_maker = InstanceDictPrimaryKeyRelatedField(
        instance_class=DecisionMaker,
        queryset=DecisionMaker.objects.filter(),
        related_serializer=DecisionMakerSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = InfillDevelopmentCompensationDecision
        fields = (
            "id",
            "reference_number",
            "decision_maker",
            "decision_date",
            "section",
        )


class InfillDevelopmentCompensationIntendedUseSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    intended_use = IntendedUseSerializer()

    class Meta:
        model = InfillDevelopmentCompensationIntendedUse
        fields = ("id", "intended_use", "floor_m2", "amount_per_floor_m2")


class InfillDevelopmentCompensationIntendedUseCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=IntendedUse,
        queryset=IntendedUse.objects.filter(),
        related_serializer=IntendedUseSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = InfillDevelopmentCompensationIntendedUse
        fields = ("id", "intended_use", "floor_m2", "amount_per_floor_m2")


class InfillDevelopmentCompensationAttachmentSerializer(
    FileSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = InfillDevelopmentCompensationAttachment
        fields = (
            "id",
            "file",
            "filename",
            "uploader",
            "uploaded_at",
            "infill_development_compensation_lease",
        )
        download_url_name = "infilldevelopmentcompensationattachment-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class InfillDevelopmentCompensationAttachmentCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = InfillDevelopmentCompensationAttachment
        fields = (
            "id",
            "file",
            "uploader",
            "uploaded_at",
            "infill_development_compensation_lease",
        )
        read_only_fields = ("uploaded_at",)


class InfillDevelopmentCompensationLeaseSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    lease = LeaseSuccinctSerializer()
    decisions = InfillDevelopmentCompensationDecisionSerializer(many=True)
    intended_uses = InfillDevelopmentCompensationIntendedUseSerializer(many=True)
    attachments = InfillDevelopmentCompensationAttachmentSerializer(many=True)

    class Meta:
        model = InfillDevelopmentCompensationLease
        fields = (
            "id",
            "lease",
            "note",
            "monetary_compensation_amount",
            "compensation_investment_amount",
            "increase_in_value",
            "part_of_the_increase_in_value",
            "discount_in_rent",
            "year",
            "sent_to_sap_date",
            "paid_date",
            "decisions",
            "intended_uses",
            "attachments",
        )


class InfillDevelopmentCompensationLeaseCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    lease = InstanceDictPrimaryKeyRelatedField(
        instance_class=Lease,
        queryset=Lease.objects.all(),
        related_serializer=LeaseSuccinctSerializer,
    )
    decisions = InfillDevelopmentCompensationDecisionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    intended_uses = InfillDevelopmentCompensationIntendedUseCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    attachments = InfillDevelopmentCompensationAttachmentSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = InfillDevelopmentCompensationLease
        fields = (
            "id",
            "lease",
            "note",
            "monetary_compensation_amount",
            "compensation_investment_amount",
            "increase_in_value",
            "part_of_the_increase_in_value",
            "discount_in_rent",
            "year",
            "sent_to_sap_date",
            "paid_date",
            "decisions",
            "intended_uses",
            "attachments",
        )


class InfillDevelopmentCompensationSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    user = UserSerializer()
    infill_development_compensation_leases = (
        InfillDevelopmentCompensationLeaseSerializer(many=True)
    )

    class Meta:
        model = InfillDevelopmentCompensation
        fields = (
            "id",
            "name",
            "reference_number",
            "detailed_plan_identifier",
            "user",
            "state",
            "lease_contract_change_date",
            "note",
            "infill_development_compensation_leases",
            "geometry",
        )


class InfillDevelopmentCompensationCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    user = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
    )
    infill_development_compensation_leases = (
        InfillDevelopmentCompensationLeaseCreateUpdateSerializer(
            many=True, required=False, allow_null=True
        )
    )

    class Meta:
        model = InfillDevelopmentCompensation
        fields = (
            "id",
            "name",
            "reference_number",
            "detailed_plan_identifier",
            "user",
            "state",
            "lease_contract_change_date",
            "note",
            "infill_development_compensation_leases",
            "geometry",
        )
