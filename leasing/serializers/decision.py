from rest_framework import serializers

from ..models import Condition, ConditionType, Decision, DecisionMaker
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class ConditionTypeSerializer(NameModelSerializer):
    class Meta:
        model = ConditionType
        fields = '__all__'


class ConditionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Condition
        fields = ('id', 'type', 'supervision_date', 'supervised_date', 'description')


class ConditionCreateUpdateSerializer(serializers.ModelSerializer):
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


class DecisionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    conditions = ConditionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Decision
        fields = ('id', 'reference_number', 'decision_maker', 'decision_date', 'section', 'type', 'description',
                  'conditions')


class DecisionCreateUpdateSerializer(UpdateNestedMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
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
