import copy
from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import Field


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

            if field_source is None:
                fields[field_name] = serializers.ReadOnlyField()
            elif callable(field_source):
                setattr(self, "get_{}".format(field_name), field_source)
                fields[field_name] = serializers.SerializerMethodField()
            else:
                fields[field_name] = serializers.ReadOnlyField(source=field_source)

        return fields
