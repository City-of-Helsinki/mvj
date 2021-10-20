from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers

from credit_integration.enums import CreditDecisionStatus
from credit_integration.models import CreditDecision, CreditDecisionReason
from field_permissions.serializers import FieldPermissionsSerializerMixin
from users.models import User


class ClaimantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class CreditDecisionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditDecisionReason
        fields = ["reason_code", "reason"]


class CreditDecisionSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    claimant = ClaimantSerializer()
    reasons = CreditDecisionReasonSerializer(many=True)

    class Meta:
        model = CreditDecision
        fields = [
            "id",
            "claimant",
            "created_at",
            "status",
            "business_id",
            "official_name",
            "address",
            "phone_number",
            "business_entity",
            "operation_start_date",
            "industry_code",
            "reasons",
        ]


class CreditDecisionReasonConsumerSerializer(serializers.Serializer):
    reason_code = serializers.CharField(max_length=3)
    reason = serializers.CharField(max_length=255)

    class Meta:
        fields = ["reason_code", "reason"]


class CreditDecisionConsumerSerializer(serializers.Serializer):
    status = EnumField(enum=CreditDecisionStatus, required=False)
    official_name = serializers.CharField(max_length=255)
    claimant = ClaimantSerializer()
    reasons = CreditDecisionReasonConsumerSerializer(many=True)

    class Meta:
        fields = [
            "claimant",
            "status",
            "official_name",
            "reasons",
        ]
