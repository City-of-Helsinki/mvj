from collections import OrderedDict

from rest_framework import serializers


class ReportOutputSerializer(serializers.Serializer):
    def __init__(self, *args, output_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_fields = output_fields

    def get_fields(self):
        fields = OrderedDict()

        for field_name, field_attrs in self.output_fields.items():
            field_source = field_attrs.get('source', None)

            if field_source is None:
                fields[field_name] = serializers.ReadOnlyField()
            elif callable(field_source):
                setattr(self, 'get_{}'.format(field_name), field_source)
                fields[field_name] = serializers.SerializerMethodField()
            else:
                fields[field_name] = serializers.ReadOnlyField(source=field_source)

        return fields
