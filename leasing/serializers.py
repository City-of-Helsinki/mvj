from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from leasing.models import Lease


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    identifier = serializers.ReadOnlyField(source='identifier_string')

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
