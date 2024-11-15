from django.utils.translation import gettext_lazy as _
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import (
    DueDatesType,
    RentAdjustmentAmountType,
    RentCycle,
    RentType,
    is_akv_or_kuva_service_unit_id,
)
from leasing.models import (
    ContractRent,
    Decision,
    FixedInitialYearRent,
    Index,
    IndexAdjustedRent,
    LeaseBasisOfRent,
    PayableRent,
    ReceivableType,
    Rent,
    RentAdjustment,
    RentDueDate,
    RentIntendedUse,
)
from leasing.models.rent import (
    EqualizedRent,
    LeaseBasisOfRentManagementSubvention,
    LeaseBasisOfRentTemporarySubvention,
    ManagementSubvention,
    ManagementSubventionFormOfManagement,
    TemporarySubvention,
)
from leasing.serializers.receivable_type import ReceivableTypeSerializer
from leasing.serializers.utils import validate_seasonal_day_for_month
from users.serializers import UserSerializer

from .decision import DecisionSerializer
from .utils import (
    DayMonthField,
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)


class RentIntendedUseSerializer(NameModelSerializer):
    class Meta:
        model = RentIntendedUse
        fields = "__all__"


class RentDueDateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RentDueDate
        fields = ("id", "day", "month")

    def validate(self, data):
        validate_seasonal_day_for_month(data.get("day"), data.get("month"))
        return data


class FixedInitialYearRentSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=RentIntendedUse,
        queryset=RentIntendedUse.objects.all(),
        related_serializer=RentIntendedUseSerializer,
    )

    class Meta:
        model = FixedInitialYearRent
        fields = ("id", "amount", "intended_use", "start_date", "end_date")

    def is_valid_end_date(self, rent: Rent, end_date):
        if not rent or not rent.cycle or not end_date:
            return True

        if (
            rent.cycle == RentCycle.JANUARY_TO_DECEMBER
            and end_date.day == 31
            and end_date.month == 12
        ):
            return True

        if (
            rent.cycle == RentCycle.APRIL_TO_MARCH
            and end_date.day == 31
            and end_date.month == 3
        ):
            return True

        return False

    def create(self, validated_data):
        if not self.is_valid_end_date(
            validated_data.get("rent"), validated_data.get("end_date")
        ):
            raise serializers.ValidationError(
                _("Fixed initial rent end date must match rent cycle end date")
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if not self.is_valid_end_date(
            validated_data.get("rent"), validated_data.get("end_date")
        ):
            raise serializers.ValidationError(
                _("Fixed initial rent end date must match rent cycle end date")
            )

        return super().update(instance, validated_data)


class IndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Index
        fields = ("id", "number", "year", "month")


class ContractRentSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=RentIntendedUse,
        queryset=RentIntendedUse.objects.all(),
        related_serializer=RentIntendedUseSerializer,
    )
    index = InstanceDictPrimaryKeyRelatedField(
        instance_class=Index,
        queryset=Index.objects.all(),
        related_serializer=IndexSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ContractRent
        fields = (
            "id",
            "amount",
            "period",
            "intended_use",
            "index",
            "base_amount",
            "base_amount_period",
            "base_year_rent",
            "start_date",
            "end_date",
        )

    def to_internal_value(self, data):
        if "amount" in data and "base_amount" not in data:
            data["base_amount"] = data["amount"]

        if "period" in data and "base_amount_period" not in data:
            data["base_amount_period"] = data["period"]

        return super().to_internal_value(data)

    def _is_valid_index(self, rent: Rent, index):
        if rent.type != RentType.INDEX2022:
            return True

        return bool(index)

    def create(self, validated_data):
        rent = validated_data.get("rent")

        if rent and not self._is_valid_index(rent, validated_data.get("index")):
            raise serializers.ValidationError(
                _("Index is mandatory if the rent type is Index")
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        rent = validated_data.get("rent")

        if rent and not self._is_valid_index(rent, validated_data.get("index")):
            raise serializers.ValidationError(
                _("Index is mandatory if the rent type is Index")
            )

        return super().update(instance, validated_data)


class IndexAdjustedRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = IndexAdjustedRent
        fields = ("id", "amount", "intended_use", "start_date", "end_date", "factor")


class PayableRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = PayableRent
        fields = (
            "id",
            "amount",
            "start_date",
            "end_date",
            "difference_percent",
            "calendar_year_rent",
        )


class EqualizedRentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = EqualizedRent
        fields = (
            "id",
            "start_date",
            "end_date",
            "payable_amount",
            "equalized_payable_amount",
            "equalization_factor",
        )


class ManagementSubventionFormOfManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementSubventionFormOfManagement
        fields = "__all__"


class ManagementSubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = ManagementSubventionFormOfManagementSerializer(required=False)

    class Meta:
        model = ManagementSubvention
        fields = ("id", "management", "subvention_amount")


class ManagementSubventionCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = InstanceDictPrimaryKeyRelatedField(
        instance_class=ManagementSubventionFormOfManagement,
        queryset=ManagementSubventionFormOfManagement.objects.all(),
        related_serializer=ManagementSubventionFormOfManagementSerializer,
    )

    class Meta:
        model = ManagementSubvention
        fields = ("id", "management", "subvention_amount")


class TemporarySubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TemporarySubvention
        fields = ("id", "description", "subvention_percent")


class RentAdjustmentSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    decision = DecisionSerializer(required=False)
    intended_use = RentIntendedUseSerializer()
    management_subventions = ManagementSubventionSerializer(
        many=True, required=False, allow_null=True
    )
    temporary_subventions = TemporarySubventionSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = RentAdjustment
        fields = (
            "id",
            "type",
            "intended_use",
            "start_date",
            "end_date",
            "full_amount",
            "amount_type",
            "amount_left",
            "decision",
            "note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
        )


class RentAdjustmentCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(
        instance_class=Decision,
        queryset=Decision.objects.all(),
        related_serializer=DecisionSerializer,
        required=False,
        allow_null=True,
    )
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=RentIntendedUse,
        queryset=RentIntendedUse.objects.all(),
        related_serializer=RentIntendedUseSerializer,
    )
    management_subventions = ManagementSubventionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    temporary_subventions = TemporarySubventionSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = RentAdjustment
        fields = (
            "id",
            "type",
            "intended_use",
            "start_date",
            "end_date",
            "full_amount",
            "amount_type",
            "amount_left",
            "decision",
            "note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
        )
        read_only_fields = ("amount_left",)

    def validate(self, data):
        if (
            data.get("amount_type") == RentAdjustmentAmountType.AMOUNT_TOTAL
            and data.get("end_date") is not None
        ):
            raise serializers.ValidationError(
                _("Amount total adjustment type cannot have an end date")
            )

        return data


class RentSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(
        many=True, required=False, allow_null=True
    )
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    rent_adjustments = RentAdjustmentSerializer(
        many=True, required=False, allow_null=True
    )
    payable_rents = PayableRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    equalized_rents = EqualizedRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    yearly_due_dates = ListSerializer(
        child=DayMonthField(read_only=True),
        source="get_due_dates_as_daymonths",
        read_only=True,
    )

    class Meta:
        model = Rent
        fields = (
            "id",
            "type",
            "cycle",
            "index_type",
            "due_dates_type",
            "due_dates_per_year",
            "elementary_index",
            "index_rounding",
            "x_value",
            "y_value",
            "y_value_start",
            "equalization_start_date",
            "equalization_end_date",
            "amount",
            "note",
            "due_dates",
            "fixed_initial_year_rents",
            "contract_rents",
            "index_adjusted_rents",
            "rent_adjustments",
            "payable_rents",
            "equalized_rents",
            "start_date",
            "end_date",
            "yearly_due_dates",
            "seasonal_start_day",
            "seasonal_start_month",
            "seasonal_end_day",
            "seasonal_end_month",
            "manual_ratio",
            "manual_ratio_previous",
            "override_receivable_type",
        )

    def override_permission_check_field_name(self, field_name):
        if field_name == "yearly_due_dates":
            return "due_dates"

        return field_name


class RentSimpleSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Rent
        fields = (
            "id",
            "type",
            "cycle",
            "index_type",
            "due_dates_type",
            "due_dates_per_year",
            "elementary_index",
            "index_rounding",
            "x_value",
            "y_value",
            "y_value_start",
            "equalization_start_date",
            "equalization_end_date",
            "amount",
            "note",
            "start_date",
            "end_date",
            "seasonal_start_day",
            "seasonal_start_month",
            "seasonal_end_day",
            "seasonal_end_month",
            "manual_ratio",
            "manual_ratio_previous",
            "override_receivable_type",
        )


class RentCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    due_dates = RentDueDateSerializer(many=True, required=False, allow_null=True)
    fixed_initial_year_rents = FixedInitialYearRentSerializer(
        many=True, required=False, allow_null=True
    )
    contract_rents = ContractRentSerializer(many=True, required=False, allow_null=True)
    index_adjusted_rents = IndexAdjustedRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    rent_adjustments = RentAdjustmentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    payable_rents = PayableRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    equalized_rents = EqualizedRentSerializer(
        many=True, required=False, allow_null=True, read_only=True
    )
    override_receivable_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=ReceivableType,
        queryset=ReceivableType.objects.all(),
        related_serializer=ReceivableTypeSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Rent
        fields = (
            "id",
            "type",
            "cycle",
            "index_type",
            "due_dates_type",
            "due_dates_per_year",
            "elementary_index",
            "index_rounding",
            "x_value",
            "y_value",
            "y_value_start",
            "equalization_start_date",
            "equalization_end_date",
            "amount",
            "note",
            "due_dates",
            "fixed_initial_year_rents",
            "contract_rents",
            "index_adjusted_rents",
            "rent_adjustments",
            "payable_rents",
            "equalized_rents",
            "start_date",
            "end_date",
            "seasonal_start_day",
            "seasonal_start_month",
            "seasonal_end_day",
            "seasonal_end_month",
            "manual_ratio",
            "manual_ratio_previous",
            "override_receivable_type",
        )

    def validate(self, rent_data: dict):
        self.validate_seasonal_values(rent_data)
        self.validate_override_receivable_type_value(rent_data)
        return rent_data

    def validate_seasonal_values(self, rent_data: dict) -> None:
        """Raises: serializers.ValidationError"""
        seasonal_values = [
            rent_data.get("seasonal_start_day"),
            rent_data.get("seasonal_start_month"),
            rent_data.get("seasonal_end_day"),
            rent_data.get("seasonal_end_month"),
        ]

        if not all(v is None for v in seasonal_values) and any(
            v is None for v in seasonal_values
        ):
            raise serializers.ValidationError(
                _("All seasonal values are required if one is set")
            )

        if (
            all(seasonal_values)
            and rent_data.get("due_dates_type") != DueDatesType.CUSTOM
        ):
            raise serializers.ValidationError(
                _("Due dates type must be custom if seasonal dates are set")
            )

        start_day, start_month, end_day, end_month = seasonal_values
        validate_seasonal_day_for_month(start_day, start_month)
        validate_seasonal_day_for_month(end_day, end_month)

    def validate_override_receivable_type_value(self, rent_data: dict) -> None:
        """
        Override receivabletype is mandatory for AKV and KuVa leases, and not
        used by MaKe/Tontit.

        It is only used in index rents, fixed rents, and manual rents, because
        these rent types can generate automatic invoices.

        Raises: serializers.ValidationError
        """
        override_receivable_type = rent_data.get("override_receivable_type")

        if not override_receivable_type:
            # Empty override receivabletype input should be allowed, because it
            # is always empty for all MaKe rents, and those must be allowed.
            return

        elif not is_akv_or_kuva_service_unit_id(
            override_receivable_type.service_unit_id
        ):
            # All MaKe receivabletypes should be rejected regardless of rent
            # type, because MaKe doesn't use the override feature, and if any
            # other service unit would use MaKe's receivabletypes, it would be
            # a mistake.
            raise serializers.ValidationError(
                _(
                    f'Override receivabletype "{override_receivable_type.name}" was unexpected. '
                    "Override receivabletype is not used by MaKe/Tontit."
                )
            )

        elif is_akv_or_kuva_service_unit_id(override_receivable_type.service_unit_id):
            rent_type = rent_data.get("type", {})

            if rent_type in [
                RentType.INDEX,
                RentType.INDEX2022,
                RentType.FIXED,
                RentType.MANUAL,
            ]:
                # These rent types can generate automatic invoices, so they can
                # utilize the override receivabletype.
                return
            else:
                raise serializers.ValidationError(
                    _(
                        f'Override receivabletype "{override_receivable_type.name}" was unexpected. '
                        f'Rent type "{rent_type.name}" does not generate automatic invoices.'
                    )
                )

        else:
            raise serializers.ValidationError(
                _(
                    "Unhandled case in override receivabletype validation. Rejecting just in case."
                )
            )


class LeaseBasisOfRentManagementSubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    management = ManagementSubventionFormOfManagementSerializer(required=False)

    class Meta:
        model = LeaseBasisOfRentManagementSubvention
        fields = ("id", "management", "subvention_amount")


class LeaseBasisOfRentManagementSubventionCreateUpdateSerializer(
    serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    management = InstanceDictPrimaryKeyRelatedField(
        instance_class=ManagementSubventionFormOfManagement,
        queryset=ManagementSubventionFormOfManagement.objects.all(),
        related_serializer=ManagementSubventionFormOfManagementSerializer,
    )

    class Meta:
        model = LeaseBasisOfRentManagementSubvention
        fields = ("id", "management", "subvention_amount")


class LeaseBasisOfRentTemporarySubventionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LeaseBasisOfRentTemporarySubvention
        fields = ("id", "description", "subvention_percent")


class LeaseBasisOfRentSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    intended_use = RentIntendedUseSerializer()
    index = IndexSerializer()
    plans_inspected_by = UserSerializer(read_only=True)
    locked_by = UserSerializer(read_only=True)
    management_subventions = LeaseBasisOfRentManagementSubventionSerializer(
        many=True, required=False, allow_null=True
    )
    temporary_subventions = LeaseBasisOfRentTemporarySubventionSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LeaseBasisOfRent
        fields = (
            "id",
            "type",
            "intended_use",
            "area",
            "area_unit",
            "amount_per_area",
            "zone",
            "index",
            "profit_margin_percentage",
            "discount_percentage",
            "plans_inspected_at",
            "plans_inspected_by",
            "locked_at",
            "locked_by",
            "archived_at",
            "archived_note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
            "children",
        )


class LeaseBaseBasisOfRentCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    intended_use = InstanceDictPrimaryKeyRelatedField(
        instance_class=RentIntendedUse,
        queryset=RentIntendedUse.objects.all(),
        related_serializer=RentIntendedUseSerializer,
    )
    index = InstanceDictPrimaryKeyRelatedField(
        instance_class=Index,
        queryset=Index.objects.all(),
        related_serializer=IndexSerializer,
        required=False,
        allow_null=True,
    )
    management_subventions = LeaseBasisOfRentManagementSubventionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    temporary_subventions = LeaseBasisOfRentTemporarySubventionSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LeaseBasisOfRent
        fields = (
            "id",
            "intended_use",
            "area",
            "area_unit",
            "amount_per_area",
            "index",
            "profit_margin_percentage",
            "discount_percentage",
            "plans_inspected_at",
            "locked_at",
            "archived_at",
            "archived_note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
            "zone",
            "type",
            "children",
        )

    def validate(self, data):
        if data.get("id"):
            try:
                instance = LeaseBasisOfRent.objects.get(pk=data["id"])
            except LeaseBasisOfRent.DoesNotExist:
                raise ValidationError(
                    _("Basis of rent item id {} not found").format(data["id"])
                )

            # Only "locked_at" field can be edited on locked items
            if instance.locked_at:
                if set(data.keys()) != {"id", "locked_at"}:
                    raise ValidationError(_("Can't edit locked basis of rent item"))

                # Set all required fields to their current value to pass validation
                data["intended_use"] = instance.intended_use
                data["area"] = instance.area
                data["area_unit"] = instance.area_unit
                data["index"] = instance.index

        if "locked_at" in data:
            if data["locked_at"]:
                data["locked_by"] = self.context["request"].user
            else:
                data["locked_by"] = None

        if "plans_inspected_at" in data:
            if data["plans_inspected_at"]:
                data["plans_inspected_by"] = self.context["request"].user
            else:
                data["plans_inspected_by"] = None

        return data


class LeaseSubBasisOfRentCreateUpdateSerializer(
    LeaseBaseBasisOfRentCreateUpdateSerializer
):
    class Meta:
        model = LeaseBasisOfRent
        fields = (
            "id",
            "intended_use",
            "area",
            "area_unit",
            "amount_per_area",
            "index",
            "profit_margin_percentage",
            "discount_percentage",
            "plans_inspected_at",
            "locked_at",
            "archived_at",
            "archived_note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
            "zone",
            "type",
        )
        extra_kwargs = {"area_unit": {"required": True}}

    def create(self, validated_data):
        validated_data["lease"] = validated_data.get("parent").lease
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["lease"] = validated_data.get("parent").lease
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return super(LeaseSubBasisOfRentCreateUpdateSerializer, self).to_representation(
            instance
        )["id"]


class LeaseBasisOfRentCreateUpdateSerializer(
    LeaseBaseBasisOfRentCreateUpdateSerializer
):

    children = LeaseSubBasisOfRentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LeaseBasisOfRent
        fields = (
            "id",
            "intended_use",
            "area",
            "area_unit",
            "amount_per_area",
            "index",
            "profit_margin_percentage",
            "discount_percentage",
            "plans_inspected_at",
            "locked_at",
            "archived_at",
            "archived_note",
            "subvention_type",
            "subvention_base_percent",
            "subvention_graduated_percent",
            "management_subventions",
            "temporary_subventions",
            "zone",
            "type",
            "children",
        )
