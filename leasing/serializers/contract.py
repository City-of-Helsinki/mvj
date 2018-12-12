from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Contract, ContractChange, ContractType, Decision, MortgageDocument
from .decision import DecisionSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class MortgageDocumentSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = MortgageDocument
        fields = ('id', 'number', 'date', 'note')


class ContractChangeSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ContractChange
        fields = ('id', 'signing_date', 'sign_by_date', 'first_call_sent', 'second_call_sent', 'third_call_sent',
                  'description', 'decision')


class ContractChangeCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision, queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer, required=False)

    class Meta:
        model = ContractChange
        fields = ('id', 'signing_date', 'sign_by_date', 'first_call_sent', 'second_call_sent', 'third_call_sent',
                  'description', 'decision')


class ContractTypeSerializer(NameModelSerializer):
    class Meta:
        model = ContractType
        fields = '__all__'


class ContractSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    mortgage_documents = MortgageDocumentSerializer(many=True, required=False, allow_null=True)
    contract_changes = ContractChangeSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Contract
        fields = ('id', 'type', 'contract_number', 'signing_date', 'signing_note', 'is_readjustment_decision',
                  'decision', 'ktj_link', 'collateral_number', 'collateral_start_date', 'collateral_end_date',
                  'collateral_note', 'institution_identifier', 'contract_changes', 'mortgage_documents')


class ContractCreateUpdateSerializer(UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(instance_class=ContractType, queryset=ContractType.objects.all(),
                                              related_serializer=ContractTypeSerializer)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision,
                                                  queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer,
                                                  required=False)
    mortgage_documents = MortgageDocumentSerializer(many=True, required=False, allow_null=True)
    contract_changes = ContractChangeCreateUpdateSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Contract
        fields = ('id', 'type', 'contract_number', 'signing_date', 'signing_note', 'is_readjustment_decision',
                  'decision', 'ktj_link', 'collateral_number', 'collateral_start_date', 'collateral_end_date',
                  'collateral_note', 'institution_identifier', 'contract_changes', 'mortgage_documents')
