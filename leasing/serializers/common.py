from rest_framework import serializers

from leasing.models import Management


class ManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Management
        fields = "__all__"
