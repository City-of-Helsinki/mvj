from django.urls import reverse
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from leasing.models import DecisionMaker, IntendedUse, Lease
from leasing.serializers.decision import DecisionMakerSerializer
from leasing.serializers.lease import IntendedUseSerializer, LeaseSuccinctSerializer
from leasing.serializers.utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin
from users.models import User
from users.serializers import UserSerializer

from ..models import (
    InfillDevelopmentCompensation, InfillDevelopmentCompensationAttachment, InfillDevelopmentCompensationDecision,
    InfillDevelopmentCompensationIntendedUse, InfillDevelopmentCompensationLease)


class InfillDevelopmentCompensationDecisionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision_maker = DecisionMakerSerializer()

    class Meta:
        model = InfillDevelopmentCompensationDecision
        fields = ('id', 'reference_number', 'decision_maker', 'decision_date', 'section')


class InfillDevelopmentCompensationDecisionCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision_maker = InstanceDictPrimaryKeyRelatedField(
        instance_class=DecisionMaker, queryset=DecisionMaker.objects.filter(),
        related_serializer=DecisionMakerSerializer, required=False, allow_null=True)

    class Meta:
        model = InfillDevelopmentCompensationDecision
        fields = ('id', 'reference_number', 'decision_maker', 'decision_date', 'section')


class InfillDevelopmentCompensationIntendedUseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = IntendedUseSerializer()

    class Meta:
        model = InfillDevelopmentCompensationIntendedUse
        fields = ('id', 'intended_use', 'floor_m2', 'amount_per_floor_m2')


class InfillDevelopmentCompensationIntendedUseCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=IntendedUse, queryset=IntendedUse.objects.filter(),
                                                      related_serializer=IntendedUseSerializer, required=False,
                                                      allow_null=True)

    class Meta:
        model = InfillDevelopmentCompensationIntendedUse
        fields = ('id', 'intended_use', 'floor_m2', 'amount_per_floor_m2')


class InfillDevelopmentCompensationAttachmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField('get_attachment_url')

    def get_attachment_url(self, obj):
        if not obj or not obj.file:
            return None

        url = reverse('infilldevelopmentcompensationattachment-download', args=[obj.id])

        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url

    class Meta:
        model = InfillDevelopmentCompensationAttachment
        fields = ('id', 'file', 'uploader', 'uploaded_at', 'infill_development_compensation_lease')


class InfillDevelopmentCompensationAttachmentCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = InfillDevelopmentCompensationAttachment
        fields = ('id', 'file', 'uploader', 'uploaded_at', 'infill_development_compensation_lease')
        read_only_fields = ('uploaded_at', )


class InfillDevelopmentCompensationLeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    lease = LeaseSuccinctSerializer()
    decisions = InfillDevelopmentCompensationDecisionSerializer(many=True)
    intended_uses = InfillDevelopmentCompensationIntendedUseSerializer(many=True)
    attachments = InfillDevelopmentCompensationAttachmentSerializer(many=True)

    class Meta:
        model = InfillDevelopmentCompensationLease
        fields = ('id', 'lease', 'note', 'monetary_compensation_amount', 'compensation_investment_amount',
                  'increase_in_value', 'part_of_the_increase_in_value', 'discount_in_rent', 'year', 'sent_to_sap_date',
                  'paid_date', 'decisions', 'intended_uses', 'attachments')


class InfillDevelopmentCompensationLeaseCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin,
                                                               serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    lease = InstanceDictPrimaryKeyRelatedField(instance_class=Lease, queryset=Lease.objects.all(),
                                               related_serializer=LeaseSuccinctSerializer)
    decisions = InfillDevelopmentCompensationDecisionCreateUpdateSerializer(many=True, required=False, allow_null=True)
    intended_uses = InfillDevelopmentCompensationIntendedUseCreateUpdateSerializer(many=True, required=False,
                                                                                   allow_null=True)

    class Meta:
        model = InfillDevelopmentCompensationLease
        fields = ('id', 'lease', 'note', 'monetary_compensation_amount', 'compensation_investment_amount',
                  'increase_in_value', 'part_of_the_increase_in_value', 'discount_in_rent', 'year', 'sent_to_sap_date',
                  'paid_date', 'decisions', 'intended_uses')


class InfillDevelopmentCompensationSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = UserSerializer()
    infill_development_compensation_leases = InfillDevelopmentCompensationLeaseSerializer(many=True)

    class Meta:
        model = InfillDevelopmentCompensation
        fields = ('id', 'name', 'reference_number', 'detailed_plan_identifier', 'user', 'state',
                  'lease_contract_change_date', 'note', 'infill_development_compensation_leases')


class InfillDevelopmentCompensationCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin,
                                                          serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    user = InstanceDictPrimaryKeyRelatedField(instance_class=User, queryset=User.objects.all(),
                                              related_serializer=UserSerializer)
    infill_development_compensation_leases = InfillDevelopmentCompensationLeaseCreateUpdateSerializer(
        many=True, required=False, allow_null=True)

    class Meta:
        model = InfillDevelopmentCompensation
        fields = ('id', 'name', 'reference_number', 'detailed_plan_identifier', 'user', 'state',
                  'lease_contract_change_date', 'note', 'infill_development_compensation_leases')
