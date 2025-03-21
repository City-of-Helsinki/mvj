from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OneToOneField, OneToOneRel
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
    is_forward: bool = False,
):
    """
    is_forward (bool): Indicates whether the relationship is a forward relationship.
    If set to True, the related instance is assigned back to the parent instance
    after being saved, and the parent instance is updated accordingly.
    """

    if hasattr(instance, related_name):
        related_instance = getattr(instance, related_name)
    else:
        related_instance = None

    if not validated_data:
        if is_forward is True:
            # If the relationship is forward,
            # then related_instance existed before and no deletion is necessary.
            return

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

    related_instance = serializer.save(**{remote_name: instance})
    if is_forward is True:
        # If related_instance is a forward relation from instance,
        # set the related_instance to instance
        setattr(instance, related_name, related_instance)
        instance.save()


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
                elif isinstance(related_field, OneToOneField):
                    nested[field_name] = {
                        "data": validated_data.pop(field_name, None),
                        "remote_name": related_field.remote_field.name,
                        "one_to_one": True,
                        "is_forward": True,
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
                    is_forward=nested_datum.get("is_forward", False),
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
