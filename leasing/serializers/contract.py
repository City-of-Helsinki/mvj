from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models.contract import Collateral, CollateralType

from ..models import Contract, ContractChange, ContractType, Decision
from .decision import DecisionSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class ContractChangeSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ContractChange
        fields = ('id', 'signing_date', 'sign_by_date', 'first_call_sent', 'second_call_sent', 'third_call_sent',
                  'description', 'decision')


class ContractChangeCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision, queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer, required=False,
                                                  allow_null=True)

    class Meta:
        model = ContractChange
        fields = ('id', 'signing_date', 'sign_by_date', 'first_call_sent', 'second_call_sent', 'third_call_sent',
                  'description', 'decision')


class CollateralTypeSerializer(NameModelSerializer):
    class Meta:
        model = CollateralType
        fields = '__all__'


class CollateralSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Collateral
        exclude = ('contract',)


class CollateralCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(instance_class=CollateralType, queryset=CollateralType.objects.all(),
                                              related_serializer=CollateralTypeSerializer)

    class Meta:
        model = Collateral
        exclude = ('contract',)


class ContractTypeSerializer(NameModelSerializer):
    class Meta:
        model = ContractType
        fields = '__all__'


class ContractSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contract_changes = ContractChangeSerializer(many=True, required=False, allow_null=True)
    collaterals = CollateralSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Contract
        fields = ('id', 'type', 'contract_number', 'signing_date', 'sign_by_date', 'signing_note',
                  'is_readjustment_decision', 'decision', 'ktj_link', 'institution_identifier',
                  'first_call_sent', 'second_call_sent', 'third_call_sent', 'contract_changes',
                  'collaterals')


class ContractCreateUpdateSerializer(UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(instance_class=ContractType, queryset=ContractType.objects.all(),
                                              related_serializer=ContractTypeSerializer)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision,
                                                  queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer,
                                                  required=False, allow_null=True)
    contract_changes = ContractChangeCreateUpdateSerializer(many=True, required=False, allow_null=True)
    collaterals = CollateralCreateUpdateSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Contract
        fields = ('id', 'type', 'contract_number', 'signing_date', 'sign_by_date', 'signing_note',
                  'is_readjustment_decision', 'decision', 'ktj_link', 'institution_identifier',
                  'first_call_sent', 'second_call_sent', 'third_call_sent', 'contract_changes',
                  'collaterals')
