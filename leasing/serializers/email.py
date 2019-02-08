from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from leasing.enums import EmailLogType
from leasing.models import EmailLog, Lease
from leasing.serializers.lease import LeaseSuccinctSerializer
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField
from users.models import User
from users.serializers import UserSerializer


class EmailLogSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    user = UserSerializer()
    recipients = UserSerializer(many=True)

    class Meta:
        model = EmailLog
        exclude = ('object_id', 'content_type')


class SendEmailSerializer(EnumSupportSerializerMixin, serializers.Serializer):
    type = EnumField(enum=EmailLogType, required=True)
    recipients = PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    text = serializers.CharField()
    lease = InstanceDictPrimaryKeyRelatedField(instance_class=Lease, queryset=Lease.objects.all(),
                                               related_serializer=LeaseSuccinctSerializer, required=False)
