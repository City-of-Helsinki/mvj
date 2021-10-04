from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

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
