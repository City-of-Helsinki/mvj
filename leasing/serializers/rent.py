from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import DueDatesType, RentAdjustmentAmountType, RentCycle
from leasing.models import Index, Management
from leasing.models.rent import (
    EqualizedRent, LeaseBasisOfRentManagementSubvention, LeaseBasisOfRentTemporarySubvention, ManagementSubvention,
    TemporarySubvention)
from leasing.serializers.common import ManagementSerializer
from users.serializers import UserSerializer

from ..models import (
    ContractRent, Decision, FixedInitialYearRent, IndexAdjustedRent, LeaseBasisOfRent, PayableRent, Rent,
    RentAdjustment, RentDueDate, RentIntendedUse)
from .decision import DecisionSerializer
from .utils import DayMonthField, InstanceDictPrimaryKeyRelatedField, NameModelSerializer, UpdateNestedMixin


class RentIntendedUseSerializer(NameModelSerializer):
    class Meta:
        model = RentIntendedUse
        fields = '__all__'


class RentDueDateSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RentDueDate
        fields = ('id', 'day', 'month')


class FixedInitialYearRentSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)

    class Meta:
        model = FixedInitialYearRent
        fields = ('id', 'amount', 'intended_use', 'start_date', 'end_date')

    def is_valid_end_date(self, rent, end_date):
        if not rent or not rent.cycle or not end_date:
            return True

        if rent.cycle == RentCycle.JANUARY_TO_DECEMBER and end_date.day == 31 and end_date.month == 12:
            return True

        if rent.cycle == RentCycle.APRIL_TO_MARCH and end_date.day == 31 and end_date.month == 3:
            return True

        return False

    def create(self, validated_data):
        if not self.is_valid_end_date(validated_data.get('rent'), validated_data.get('end_date')):
            raise serializers.ValidationError(_("Fixed initial rent end date must match rent cycle end date"))

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if not self.is_valid_end_date(validated_data.get('rent'), validated_data.get('end_date')):
            raise serializers.ValidationError(_("Fixed initial rent end date must match rent cycle end date"))

        return super().update(instance, validated_data)


class ContractRentSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer):
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
        fields = ('id', 'amount', 'start_date', 'end_date', 'difference_percent', 'calendar_year_rent')


class EqualizedRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EqualizedRent
        fields = ('id', 'start_date', 'end_date', 'payable_amount', 'equalized_payable_amount', 'equalization_factor')


class ManagementSubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = ManagementSerializer(required=False)

    class Meta:
        model = ManagementSubvention
        fields = ('id', 'management', 'subvention_percent')


class ManagementSubventionCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = InstanceDictPrimaryKeyRelatedField(instance_class=Management, queryset=Management.objects.all(),
                                                    related_serializer=ManagementSerializer)

    class Meta:
        model = ManagementSubvention
        fields = ('id', 'management', 'subvention_percent')


class TemporarySubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TemporarySubvention
        fields = ('id', 'description', 'subvention_percent')


class RentAdjustmentSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                               serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision = DecisionSerializer(required=False)
    intended_use = RentIntendedUseSerializer()
    management_subventions = ManagementSubventionSerializer(many=True, required=False, allow_null=True)
    temporary_subventions = TemporarySubventionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = RentAdjustment
        fields = ('id', 'type', 'intended_use', 'start_date', 'end_date', 'full_amount', 'amount_type', 'amount_left',
                  'decision', 'note', 'subvention_type', 'subvention_base_percent', 'subvention_graduated_percent',
                  'management_subventions', 'temporary_subventions')


class RentAdjustmentCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin,
                                           FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(instance_class=Decision, queryset=Decision.objects.all(),
                                                  related_serializer=DecisionSerializer, required=False,
                                                  allow_null=True)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)
    management_subventions = ManagementSubventionCreateUpdateSerializer(many=True, required=False, allow_null=True)
    temporary_subventions = TemporarySubventionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = RentAdjustment
        fields = ('id', 'type', 'intended_use', 'start_date', 'end_date', 'full_amount', 'amount_type', 'amount_left',
                  'decision', 'note', 'subvention_type', 'subvention_base_percent', 'subvention_graduated_percent',
                  'management_subventions', 'temporary_subventions')
        read_only_fields = ('amount_left', )

    def validate(self, data):
        if data.get('amount_type') == RentAdjustmentAmountType.AMOUNT_TOTAL and data.get('end_date') is not None:
            raise serializers.ValidationError(_("Amount total adjustment type cannot have an end date"))

        return data


class RentSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                     serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(many=True, required=False, allow_null=True)
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    rent_adjustments = RentAdjustmentSerializer(many=True, required=False, allow_null=True)
    payable_rents = PayableRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    equalized_rents = EqualizedRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    yearly_due_dates = ListSerializer(child=DayMonthField(read_only=True), source='get_due_dates_as_daymonths',
                                      read_only=True)

    class Meta:
        model = Rent
        fields = ('id', 'type', 'cycle', 'index_type', 'due_dates_type', 'due_dates_per_year', 'elementary_index',
                  'index_rounding', 'x_value', 'y_value', 'y_value_start', 'equalization_start_date',
                  'equalization_end_date', 'amount', 'note', 'due_dates', 'fixed_initial_year_rents', 'contract_rents',
                  'index_adjusted_rents', 'rent_adjustments', 'payable_rents', 'equalized_rents', 'start_date',
                  'end_date', 'yearly_due_dates', 'seasonal_start_day', 'seasonal_start_month', 'seasonal_end_day',
                  'seasonal_end_month', 'manual_ratio', 'manual_ratio_previous')

    def override_permission_check_field_name(self, field_name):
        if field_name == 'yearly_due_dates':
            return 'due_dates'

        return field_name


class RentSimpleSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                           serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Rent
        fields = ('id', 'type', 'cycle', 'index_type', 'due_dates_type', 'due_dates_per_year', 'elementary_index',
                  'index_rounding', 'x_value', 'y_value', 'y_value_start', 'equalization_start_date',
                  'equalization_end_date', 'amount', 'note', 'start_date', 'end_date', 'seasonal_start_day',
                  'seasonal_start_month', 'seasonal_end_day', 'seasonal_end_month', 'manual_ratio',
                  'manual_ratio_previous')


class RentCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                                 serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(many=True, required=False, allow_null=True)
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    rent_adjustments = RentAdjustmentCreateUpdateSerializer(many=True, required=False, allow_null=True)
    payable_rents = PayableRentSerializer(many=True, required=False, allow_null=True, read_only=True)
    equalized_rents = EqualizedRentSerializer(many=True, required=False, allow_null=True, read_only=True)

    class Meta:
        model = Rent
        fields = ('id', 'type', 'cycle', 'index_type', 'due_dates_type', 'due_dates_per_year', 'elementary_index',
                  'index_rounding', 'x_value', 'y_value', 'y_value_start', 'equalization_start_date',
                  'equalization_end_date', 'amount', 'note', 'due_dates', 'fixed_initial_year_rents', 'contract_rents',
                  'index_adjusted_rents', 'rent_adjustments', 'payable_rents', 'equalized_rents', 'start_date',
                  'end_date', 'seasonal_start_day', 'seasonal_start_month', 'seasonal_end_day', 'seasonal_end_month',
                  'manual_ratio', 'manual_ratio_previous')

    def validate(self, data):
        seasonal_values = [data.get('seasonal_start_day'), data.get('seasonal_start_month'),
                           data.get('seasonal_end_day'), data.get('seasonal_end_month')]

        if not all(v is None for v in seasonal_values) and any(v is None for v in seasonal_values):
            raise serializers.ValidationError(_("All seasonal values are required if one is set"))

        if all(seasonal_values) and data.get('due_dates_type') != DueDatesType.CUSTOM:
            raise serializers.ValidationError(_("Due dates type must be custom if seasonal dates are set"))

        return data


class IndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Index
        fields = '__all__'


class LeaseBasisOfRentManagementSubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = ManagementSerializer(required=False)

    class Meta:
        model = LeaseBasisOfRentManagementSubvention
        fields = ('id', 'management', 'subvention_percent')


class LeaseBasisOfRentManagementSubventionCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = InstanceDictPrimaryKeyRelatedField(instance_class=Management, queryset=Management.objects.all(),
                                                    related_serializer=ManagementSerializer)

    class Meta:
        model = LeaseBasisOfRentManagementSubvention
        fields = ('id', 'management', 'subvention_percent')


class LeaseBasisOfRentTemporarySubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LeaseBasisOfRentTemporarySubvention
        fields = ('id', 'description', 'subvention_percent')


class LeaseBasisOfRentSerializer(EnumSupportSerializerMixin, FieldPermissionsSerializerMixin,
                                 serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = RentIntendedUseSerializer()
    index = IndexSerializer()
    plans_inspected_by = UserSerializer(read_only=True)
    locked_by = UserSerializer(read_only=True)
    management_subventions = LeaseBasisOfRentManagementSubventionSerializer(many=True, required=False, allow_null=True)
    temporary_subventions = LeaseBasisOfRentTemporarySubventionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseBasisOfRent
        fields = ('id', 'intended_use', 'area', 'area_unit', 'amount_per_area', 'index', 'profit_margin_percentage',
                  'discount_percentage', 'plans_inspected_at', 'plans_inspected_by', 'locked_at', 'locked_by',
                  'archived_at', 'archived_note', 'subvention_type', 'subvention_base_percent',
                  'subvention_graduated_percent', 'management_subventions', 'temporary_subventions')


class LeaseBasisOfRentCreateUpdateSerializer(UpdateNestedMixin, EnumSupportSerializerMixin,
                                             FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(instance_class=RentIntendedUse,
                                                      queryset=RentIntendedUse.objects.all(),
                                                      related_serializer=RentIntendedUseSerializer)
    index = InstanceDictPrimaryKeyRelatedField(instance_class=Index,
                                               queryset=Index.objects.all(),
                                               related_serializer=IndexSerializer)
    management_subventions = LeaseBasisOfRentManagementSubventionCreateUpdateSerializer(many=True, required=False,
                                                                                        allow_null=True)
    temporary_subventions = LeaseBasisOfRentTemporarySubventionSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseBasisOfRent
        fields = ('id', 'intended_use', 'area', 'area_unit', 'amount_per_area', 'index', 'profit_margin_percentage',
                  'discount_percentage', 'plans_inspected_at', 'locked_at', 'archived_at', 'archived_note',
                  'subvention_type', 'subvention_base_percent', 'subvention_graduated_percent',
                  'management_subventions', 'temporary_subventions')

    def validate(self, data):
        if data.get('id'):
            try:
                instance = LeaseBasisOfRent.objects.get(pk=data['id'])
            except LeaseBasisOfRent.DoesNotExist:
                raise ValidationError(_("Basis of rent item id {} not found").format(data['id']))

            # Only "locked_at" field can be edited on locked items
            if instance.locked_at:
                if set(data.keys()) != {'id', 'locked_at'}:
                    raise ValidationError(_("Can't edit locked basis of rent item"))

                # TODO: Who can unlock?

                # Set all required fields to their current value to pass validation
                data['intended_use'] = instance.intended_use
                data['area'] = instance.area
                data['index'] = instance.index

        if 'locked_at' in data:
            if data['locked_at']:
                data['locked_by'] = self.context['request'].user
            else:
                data['locked_by'] = None

        if 'plans_inspected_at' in data:
            if data['plans_inspected_at']:
                data['plans_inspected_by'] = self.context['request'].user
            else:
                data['plans_inspected_by'] = None

        return data
