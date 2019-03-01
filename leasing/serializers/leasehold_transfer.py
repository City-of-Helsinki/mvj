from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import LeaseholdTransfer, LeaseholdTransferParty


class LeaseholdTransferPartySerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                                       serializers.ModelSerializer):
    class Meta:
        model = LeaseholdTransferParty
        fields = ('type', 'name', 'business_id', 'national_identification_number',
                  'share_numerator', 'share_denominator',)


class LeaseholdTransferSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    properties = serializers.SlugRelatedField(
        slug_field='identifier', many=True, read_only=True)
    parties = LeaseholdTransferPartySerializer(many=True)

    class Meta:
        model = LeaseholdTransfer
        fields = ('properties', 'institution_identifier', 'decision_date', 'parties',)
