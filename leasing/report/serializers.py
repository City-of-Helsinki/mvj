import copy
from collections import OrderedDict
from decimal import ROUND_HALF_UP, Decimal

from django.utils import formats
from rest_framework import serializers
from rest_framework.fields import Field

from leasing.report.excel import FormatType


class ReportOutputSerializer(serializers.Serializer):
    """Default serializer for the report data

    Serializes fields that are passed in the output_fields keyword argument
    on instantiation."""

    def __init__(self, *args, output_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_fields = output_fields

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def get_fields(self):
        fields = OrderedDict()

        for field_name, field_attrs in self.output_fields.items():
            field = field_attrs.get("serializer_field", None)

            if field and isinstance(field, Field):
                # The field must be a copy because DRF modifies the field
                fields[field_name] = copy.deepcopy(field)
                continue

            field_source = field_attrs.get("source", None)
            format_type = field_attrs.get("format", None)

            if format_type in [
                FormatType.MONEY.value,
                FormatType.NUMBER.value,
                FormatType.PERCENTAGE.value,
                FormatType.AREA.value,
            ]:
                if callable(field_source):
                    setattr(self, "get_{}".format(field_name), field_source)
                    fields[field_name] = FormattedDecimalMethodField()
                else:
                    fields[field_name] = FormattedDecimalField(source=field_source)
            elif field_source is None:
                fields[field_name] = serializers.ReadOnlyField()
            elif callable(field_source):
                setattr(self, "get_{}".format(field_name), field_source)
                fields[field_name] = serializers.SerializerMethodField()
            else:
                fields[field_name] = serializers.ReadOnlyField(source=field_source)

        return fields


def _format_decimal_value(value):
    if value is None or value == "":
        return value

    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except (ValueError, TypeError):
            return value

    return formats.number_format(
        value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP),
        decimal_pos=2,
        use_l10n=True,
    )


class FormattedDecimalField(serializers.Field):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_representation(self, value):
        return _format_decimal_value(value)


class FormattedDecimalMethodField(serializers.SerializerMethodField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_representation(self, value):
        result = super().to_representation(value)
        return _format_decimal_value(result)
