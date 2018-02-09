from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from leasing.models import Asset, Client, Lease


class ClientSerializer(serializers.ModelSerializer):
    phone_numbers = serializers.StringRelatedField(many=True)

    class Meta:
        model = Client
        fields = '__all__'

    def to_representation(self, obj):
        data = super(ClientSerializer, self).to_representation(obj)
        # These seem to need to be collapsed into their values because
        # otherwise we get an "[Enum] is not JSON serializable" error.
        data['language'] = data['language'].value
        data['client_type'] = data['client_type'].value
        return data


class AssetSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Asset
        fields = '__all__'


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = serializers.ReadOnlyField(source='identifier_string')
    assets = AssetSerializer(read_only=True, many=True)

    def validate(self, data):
        start_date = data['start_date']
        end_date = data['end_date']

        if start_date is not None and end_date is not None:
            if start_date > end_date:
                raise ValidationError(_('Start date must be before end date.'))

        return data

    class Meta:
        model = Lease
        fields = '__all__'
