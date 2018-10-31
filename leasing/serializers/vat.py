from rest_framework import serializers

from ..models import Vat


class VatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vat
        fields = '__all__'
