from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Condition, ConditionType, Decision, DecisionMaker, DecisionType
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class ConditionTypeSerializer(NameModelSerializer):
    class Meta:
        model = ConditionType
        fields = '__all__'


class ConditionSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Condition
        fields = ('id', 'type', 'supervision_date', 'supervised_date', 'description')


class ConditionCreateUpdateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(instance_class=ConditionType, queryset=ConditionType.objects.filter(),
                                              related_serializer=ConditionTypeSerializer, required=False,
                                              allow_null=True)

    class Meta:
        model = Condition
        fields = ('id', 'type', 'supervision_date', 'supervised_date', 'description')


class DecisionMakerSerializer(NameModelSerializer):
    class Meta:
        model = DecisionMaker
        fields = '__all__'


class DecisionTypeSerializer(EnumSupportSerializerMixin, NameModelSerializer):
    class Meta:
        model = DecisionType
        fields = '__all__'


class DecisionSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    conditions = ConditionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Decision
        fields = ('id', 'lease', 'reference_number', 'decision_maker', 'decision_date', 'section', 'type',
                  'description', 'conditions')


class DecisionCreateUpdateNestedSerializer(UpdateNestedMixin, FieldPermissionsSerializerMixin,
                                           serializers.ModelSerializer):
    """This is used when the decision is added or updated inside a lease

    The lease is not included in this serializer, but set via the UpdateNestedMixin in LeaseCreateUpdateSerializer.
    """
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(instance_class=DecisionType, queryset=DecisionType.objects.filter(),
                                              related_serializer=DecisionTypeSerializer, required=False,
                                              allow_null=True)
    conditions = ConditionCreateUpdateSerializer(many=True, required=False, allow_null=True)
    decision_maker = InstanceDictPrimaryKeyRelatedField(instance_class=DecisionMaker,
                                                        queryset=DecisionMaker.objects.filter(),
                                                        related_serializer=DecisionMakerSerializer,
                                                        required=False,
                                                        allow_null=True)

    class Meta:
        model = Decision
        fields = ('id', 'reference_number', 'decision_maker', 'decision_date', 'section', 'type', 'description',
                  'conditions')


class DecisionCreateUpdateSerializer(UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    """This is used when creating a Decision separately on the decision viewset
    """
    id = serializers.IntegerField(required=False)
    conditions = ConditionCreateUpdateSerializer(many=True, required=False, allow_null=True)
    decision_maker = InstanceDictPrimaryKeyRelatedField(instance_class=DecisionMaker,
                                                        queryset=DecisionMaker.objects.filter(),
                                                        related_serializer=DecisionMakerSerializer,
                                                        required=False,
                                                        allow_null=True)

    class Meta:
        model = Decision
        fields = ('id', 'lease', 'reference_number', 'decision_maker', 'decision_date', 'section', 'type',
                  'description', 'conditions')
