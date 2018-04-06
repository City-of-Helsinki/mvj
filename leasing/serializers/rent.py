from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from ..models import (
    ContractRent, Decision, FixedInitialYearRent, IndexAdjustedRent, LeaseBasisOfRent, PayableRent, Rent,
    RentAdjustment, RentDueDate, RentIntendedUse)
from .decision import DecisionSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class RentIntendedUseSerializer(NameModelSerializer):
    class Meta:
        model = RentIntendedUse
        fields = '__all__'


class RentDueDateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RentDueDate
        fields = ('id', 'day', 'month')


class FixedInitialYearRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = FixedInitialYearRent
        fields = ('id', 'amount', 'start_date', 'end_date')


class ContractRentSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)

    class Meta:
        model = ContractRent
        fields = ('id', 'amount', 'period', 'intended_use', 'base_amount', 'base_amount_period', 'base_year_rent',
                  'start_date', 'end_date')


class IndexAdjustedRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = IndexAdjustedRent
        fields = ('id', 'amount', 'intended_use', 'start_date', 'end_date', 'factor')


class PayableRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PayableRent
        fields = ('id', 'amount', 'start_date', 'difference_percent', 'calendar_year_rent')


class RentAdjustmentSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision, queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer, required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)

    class Meta:
        model = RentAdjustment
        fields = ('id', 'type', 'intended_use', 'start_date', 'end_date', 'full_amount', 'amount_type', 'amount_left',
                  'decision', 'note')


class RentSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(many=True, required=False, allow_null=True)
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    rent_adjustments = RentAdjustmentSerializer(many=True, required=False, allow_null=True)
    payable_rents = PayableRentSerializer(many=True, required=False, allow_null=True, read_only=True)

    class Meta:
        model = Rent
        fields = ('id', 'type', 'cycle', 'index_type', 'due_dates_type', 'due_dates_per_year', 'elementary_index',
                  'index_rounding', 'x_value', 'y_value', 'y_value_start', 'equalization_start_date',
                  'equalization_end_date', 'amount', 'note', 'is_active', 'due_dates', 'fixed_initial_year_rents',
                  'contract_rents', 'index_adjusted_rents', 'rent_adjustments', 'payable_rents')


class RentCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(many=True, required=False, allow_null=True)
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    rent_adjustments = RentAdjustmentSerializer(many=True, required=False, allow_null=True)
    payable_rents = PayableRentSerializer(many=True, required=False, allow_null=True, read_only=True)

    class Meta:
        model = Rent
        fields = ('id', 'type', 'cycle', 'index_type', 'due_dates_type', 'due_dates_per_year', 'elementary_index',
                  'index_rounding', 'x_value', 'y_value', 'y_value_start', 'equalization_start_date',
                  'equalization_end_date', 'amount', 'note', 'is_active', 'due_dates', 'fixed_initial_year_rents',
                  'contract_rents', 'index_adjusted_rents', 'rent_adjustments', 'payable_rents')


class LeaseBasisOfRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)

    class Meta:
        model = LeaseBasisOfRent
        fields = ('id', 'intended_use', 'floor_m2', 'index', 'amount_per_floor_m2_index_100',
                  'amount_per_floor_m2_index', 'percent', 'year_rent_index_100', 'year_rent_index')
