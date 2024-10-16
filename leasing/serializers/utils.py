import os
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OneToOneRel
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class InstanceDictPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Like PrimaryKeyRelatedField but the id can be alternatively supplied inside a model instance or a dict.
    """

    def __init__(self, *args, **kwargs):
        self.instance_class = kwargs.pop("instance_class", None)
        self.related_serializer = kwargs.pop("related_serializer", None)

        super().__init__(**kwargs)

    def to_representation(self, obj):
        if self.related_serializer and hasattr(obj, "pk") and obj.pk:
            obj = self.get_queryset().get(pk=obj.pk)
            return self.related_serializer(obj, context=self.context).to_representation(
                obj
            )

        return super().to_representation(obj)

    def to_internal_value(self, value):
        pk = value

        if isinstance(value, dict) and "id" in value:
            pk = value["id"]

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


def sync_new_items_to_manager(new_items, manager, context):
    if not hasattr(manager, "add"):
        return

    existing_items = set(manager.all())

    for item in existing_items.difference(new_items):
        permission_name = "{}.delete_{}".format(
            manager.model._meta.app_label, manager.model._meta.model_name
        )
        if not context["request"].user.has_perm(permission_name):
            # Ignore removal of the item if the user doesn't have permission to delete
            continue

        if hasattr(manager, "remove"):
            manager.remove(item)
        else:
            item.delete()

    for item in new_items.difference(existing_items):
        manager.add(item)


def get_instance_from_default_manager(pk, model_class):
    if not pk:
        return None

    try:
        return model_class._default_manager.get(id=pk)
    except ObjectDoesNotExist:
        return None


def serializer_data_differs(serializer, original_serializer):
    for field_name in serializer.validated_data.keys():
        if (
            serializer.validated_data[field_name]
            != original_serializer.data[field_name]
        ):
            return True

    return False


def check_perm(serializer, instance):
    model_class = serializer.Meta.model

    if not instance:
        permission_name = "{}.add_{}".format(
            model_class._meta.app_label, model_class._meta.model_name
        )
        return serializer.context["request"].user.has_perm(permission_name)

    instance_serializer = serializer.__class__(instance)
    if serializer_data_differs(serializer, instance_serializer):
        permission_name = "{}.change_{}".format(
            model_class._meta.app_label, model_class._meta.model_name
        )
        return serializer.context["request"].user.has_perm(permission_name)
    else:
        return True


def instance_create_or_update_related(
    instance=None,
    related_name=None,
    serializer_class=None,
    validated_data=None,
    context=None,
):
    manager = getattr(instance, related_name)
    new_items = set()

    if validated_data is None:
        validated_data = []

    for item in validated_data:
        pk = item.pop("id", None)
        model_class = serializer_class.Meta.model

        serializer_params = {
            "data": item,
            "instance": get_instance_from_default_manager(pk, model_class),
            "context": context,
        }

        serializer = serializer_class(**serializer_params)

        if hasattr(serializer, "modify_fields_by_field_permissions"):
            serializer.modify_fields_by_field_permissions()

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            raise ValidationError({related_name: e.detail})

        if not check_perm(serializer, serializer.instance):
            # Ignore the new item if the user doesn't have permission to add
            continue

        item_instance = serializer.save(**{manager.field.name: instance})
        new_items.add(item_instance)

    sync_new_items_to_manager(new_items, manager, context)


def instance_create_or_update_related_one_to_one(
    instance=None,
    related_name=None,
    remote_name=None,
    serializer_class=None,
    validated_data=None,
    context=None,
):
    if hasattr(instance, related_name):
        related_instance = getattr(instance, related_name)
    else:
        related_instance = None

    if not validated_data:
        if related_instance:
            # TODO: Permission check when removing?
            related_instance.delete()
        return

    serializer_params = {
        "data": validated_data,
        "instance": related_instance,
        "context": context,
    }

    serializer = serializer_class(**serializer_params)

    if hasattr(serializer, "modify_fields_by_field_permissions"):
        serializer.modify_fields_by_field_permissions()

    try:
        serializer.is_valid(raise_exception=True)
    except ValidationError as e:
        raise ValidationError({related_name: e.detail})

    if not check_perm(serializer, serializer.instance):
        # Ignore the new item if the user doesn't have permission to add
        return

    serializer.save(**{remote_name: instance})


class UpdateNestedMixin:
    def extract_nested(self, validated_data):
        nested = {}
        for field_name, field in self.fields.items():
            if field_name not in validated_data:
                continue

            if isinstance(field, serializers.ModelSerializer):
                model_class = self.Meta.model
                related_field = model_class._meta.get_field(field.source)

                if isinstance(related_field, OneToOneRel):
                    nested[field_name] = {
                        "data": validated_data.pop(field_name, None),
                        "remote_name": related_field.remote_field.name,
                        "one_to_one": True,
                    }
                    continue

            if not isinstance(field, serializers.ListSerializer):
                continue

            if not isinstance(field.child, serializers.ModelSerializer):
                continue

            if field.many and field_name in validated_data:
                nested[field_name] = {
                    "data": validated_data.pop(field_name, None),
                    "one_to_one": False,
                }

        return nested

    def save_nested(self, instance, nested_data, context=None):
        for nested_name, nested_datum in nested_data.items():
            if nested_datum["one_to_one"]:
                instance_create_or_update_related_one_to_one(
                    instance=instance,
                    related_name=nested_name,
                    remote_name=nested_datum["remote_name"],
                    serializer_class=self.fields[nested_name].__class__,
                    validated_data=nested_datum["data"],
                    context=context,
                )
                continue

            instance_create_or_update_related(
                instance=instance,
                related_name=nested_name,
                serializer_class=self.fields[nested_name].child.__class__,
                validated_data=nested_datum["data"],
                context=context,
            )

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

        request = self.context.get("request", None)
        version_namespace = getattr(request, "version", "v1")
        url_name = self.Meta.download_url_name
        url = reverse(
            f"{version_namespace}:{url_name}",
            args=[obj.id],
        )

        if request is not None:
            return request.build_absolute_uri(url)

        return url

    def get_file_filename(self, obj):
        return os.path.basename(obj.file.name)


def validate_seasonal_day_for_month(day: int, month: int):
    max_days_in_month = {
        1: 31,  # January
        # Since this a generic date and not a calendar date with year, accept only 28 days for February
        2: 28,  # February (non-leap year)
        3: 31,  # March
        4: 30,  # April
        5: 31,  # May
        6: 30,  # June
        7: 31,  # July
        8: 31,  # August
        9: 30,  # September
        10: 31,  # October
        11: 30,  # November
        12: 31,  # December
    }

    if month < 1 or month > 12:
        raise ValidationError({"month": _(f"Invalid month: {month}")})

    max_day = max_days_in_month.get(month)
    if day < 1 or day > max_day:
        raise ValidationError({"day": _(f"Invalid day: {day} for month: {month}")})
