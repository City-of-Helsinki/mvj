import os
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class InstanceDictPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Like PrimaryKeyRelatedField but the id can be alternatively supplied inside a model instance or a dict.
    """

    def __init__(self, *args, **kwargs):
        self.instance_class = kwargs.pop('instance_class', None)
        self.related_serializer = kwargs.pop('related_serializer', None)

        super().__init__(**kwargs)

    def to_representation(self, obj):
        if self.related_serializer and hasattr(obj, 'pk') and obj.pk:
            obj = self.get_queryset().get(pk=obj.pk)
            return self.related_serializer(obj, context=self.context).to_representation(obj)

        return super().to_representation(obj)

    def to_internal_value(self, value):
        pk = value

        if isinstance(value, dict) and 'id' in value:
            pk = value['id']

        if self.instance_class and isinstance(value, self.instance_class):
            pk = value.id

        return super().to_internal_value(pk)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()

        if queryset is None:
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict((item.pk, self.display_value(item)) for item in queryset)


# TODO: Make permission checks when adding, changing and removing nested items
def sync_new_items_to_manager(new_items, manager):
    if not hasattr(manager, 'add'):
        return

    existing_items = set(manager.all())

    for item in existing_items.difference(new_items):
        if hasattr(manager, 'remove'):
            manager.remove(item)
        else:
            item.delete()

    for item in new_items.difference(existing_items):
        manager.add(item)


def instance_create_or_update_related(instance=None, related_name=None, serializer_class=None,
                                      validated_data=None, context=None):
    manager = getattr(instance, related_name)
    new_items = set()

    try:
        for item in validated_data:
            pk = item.pop('id', None)

            serializer_params = {
                'data': item,
                'context': context,
            }

            if pk:
                try:
                    item_instance = serializer_class.Meta.model._default_manager.get(id=pk)
                    serializer_params['instance'] = item_instance
                except ObjectDoesNotExist:
                    pass

            serializer = serializer_class(**serializer_params)

            if hasattr(serializer, 'modify_fields_by_field_permissions'):
                serializer.modify_fields_by_field_permissions()

            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as e:
                raise ValidationError({
                    related_name: e.detail
                })

            item_instance = serializer.save(**{
                manager.field.name: instance
            })

            new_items.add(item_instance)
    except TypeError:
        pass

    sync_new_items_to_manager(new_items, manager)


class UpdateNestedMixin:
    def extract_nested(self, validated_data):
        nested = {}
        for field_name, field in self.fields.items():
            if field_name not in validated_data:
                continue

            if not isinstance(field, serializers.ListSerializer):
                continue

            if not isinstance(field.child, serializers.ModelSerializer):
                continue

            if field.many and field_name in validated_data:
                nested[field_name] = validated_data.pop(field_name, None)

        return nested

    def save_nested(self, instance, nested_data, context=None):
        for nested_name, nested_datum in nested_data.items():
            instance_create_or_update_related(instance=instance, related_name=nested_name,
                                              serializer_class=self.fields[nested_name].child.__class__,
                                              validated_data=nested_datum,
                                              context=context)

    def create(self, validated_data):
        nested_data = self.extract_nested(validated_data)

        instance = super().create(validated_data)

        self.save_nested(instance, nested_data, context=self.context)

        return instance

    def update(self, instance, validated_data):
        nested_data = self.extract_nested(validated_data)

        instance = super().update(instance, validated_data)

        self.save_nested(instance, nested_data, context=self.context)

        return instance


class NameModelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField(read_only=True)


class DayMonthField(serializers.Field):
    def to_internal_value(self, data):
        pass

    def to_representation(self, instance):
        return instance.asdict()


class FileSerializerMixin:
    def get_file_url(self, obj):
        if not obj or not obj.file:
            return None

        url = reverse(self.Meta.download_url_name, args=[obj.id])

        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)

        return url

    def get_file_filename(self, obj):
        return os.path.basename(obj.file.name)
