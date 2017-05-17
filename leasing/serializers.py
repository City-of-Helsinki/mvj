from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from leasing.models import (
    Area, Contact, Decision, Invoice, LeaseBuildingFootprint, LeaseRealPropertyUnit, LeaseRealPropertyUnitAddress, Note,
    Rent, Tenant)
from users.serializers import UserSerializer

from .models import Application, ApplicationBuildingFootprint, Lease


def instance_replace_related(instance=None, instance_name=None, related_name=None, serializer_class=None,
                             validated_data=None):
    manager = getattr(instance, related_name)
    manager.all().delete()

    for item in validated_data:
        serializer = serializer_class(data=item)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            raise ValidationError({
                related_name: e.detail
            })

        item_instance = serializer.save(**{
            instance_name: instance
        })

        if item_instance and hasattr(manager, 'add'):
            manager.add(item_instance)


def instance_create_or_update_related(instance=None, instance_name=None, related_name=None, serializer_class=None,
                                      validated_data=None):
    for item in validated_data:
        pk = item.pop('id', None)
        manager = getattr(instance, related_name)

        serializer_params = {
            'data': item,
        }

        if pk:
            try:
                item_instance = manager.get(id=pk)
                serializer_params['instance'] = item_instance
            except ObjectDoesNotExist:
                pass

        serializer = serializer_class(**serializer_params)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            raise ValidationError({
                related_name: e.detail
            })

        item_instance = serializer.save(**{
            instance_name: instance
        })

        if item_instance and hasattr(manager, 'add'):
            manager.add(item_instance)


class InstanceDictPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """
    Like PrimaryKeyRelatedField but the id can be alternatively supplied inside a model instance or a dict.
    """

    def __init__(self, *args, **kwargs):
        self.instance_class = kwargs.pop('instance_class', None)

        super().__init__(**kwargs)

    def to_internal_value(self, value):
        pk = value

        if isinstance(value, dict) and 'id' in value:
            pk = value['id']

        if self.instance_class and isinstance(value, self.instance_class):
            pk = value.id

        return super().to_internal_value(pk)


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Note
        fields = '__all__'


class AreaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    notes = NoteSerializer(many=True, required=False)

    class Meta:
        model = Area
        fields = '__all__'


class ApplicationBuildingFootprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationBuildingFootprint
        fields = ('use', 'area')


class ApplicationSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    building_footprints = ApplicationBuildingFootprintSerializer(many=True, required=False)
    areas = AreaSerializer(many=True, required=False)
    notes = NoteSerializer(many=True, required=False)

    class Meta:
        model = Application
        fields = '__all__'

    def create(self, validated_data):
        building_footprints = validated_data.pop('building_footprints', [])
        areas = validated_data.pop('areas', [])
        notes = validated_data.pop('notes', [])

        instance = super().create(validated_data)

        instance_replace_related(instance=instance, instance_name='application', related_name='building_footprints',
                                 serializer_class=ApplicationBuildingFootprintSerializer,
                                 validated_data=building_footprints)

        instance_replace_related(instance=instance, instance_name='application', related_name='areas',
                                 serializer_class=AreaSerializer, validated_data=areas)

        instance_replace_related(instance=instance, instance_name='application', related_name='notes',
                                 serializer_class=NoteSerializer, validated_data=notes)

        return instance

    def update(self, instance, validated_data):
        building_footprints = validated_data.pop('building_footprints', None)
        areas = validated_data.pop('areas', None)
        notes = validated_data.pop('notes', None)

        instance.building_footprints.all().delete()

        if building_footprints:
            instance_replace_related(instance=instance, instance_name='application', related_name='building_footprints',
                                     serializer_class=ApplicationBuildingFootprintSerializer,
                                     validated_data=building_footprints)

        if areas:
            instance_create_or_update_related(instance=instance, instance_name='application', related_name='areas',
                                              serializer_class=AreaSerializer, validated_data=areas)

        if notes:
            instance_create_or_update_related(instance=instance, instance_name='application', related_name='notes',
                                              serializer_class=NoteSerializer, validated_data=notes)

        instance = super().update(instance, validated_data)

        return instance


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class LeaseBuildingFootprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseBuildingFootprint
        fields = ('use', 'area')


class DecisionSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Decision
        fields = '__all__'


class RentSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Rent
        fields = '__all__'


class TenantSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    contact = ContactSerializer()
    contact_contact = ContactSerializer(required=False, allow_null=True)
    billing_contact = ContactSerializer(required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = '__all__'


class InvoiceSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    reference_number = serializers.ReadOnlyField()
    billing_contact = ContactSerializer(required=False, allow_null=True)
    tenants = TenantSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = '__all__'


class TenantCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contact = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all())
    contact_contact = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                         required=False, allow_null=True)
    billing_contact = InstanceDictPrimaryKeyRelatedField(instance_class=Contact, queryset=Contact.objects.all(),
                                                         required=False, allow_null=True)

    class Meta:
        model = Tenant
        fields = ('id', 'contact', 'contact_contact', 'billing_contact', 'share')


class LeaseRealPropertyUnitAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseRealPropertyUnitAddress
        fields = ('address',)


class LeaseRealPropertyUnitSerializer(serializers.ModelSerializer):
    addresses = LeaseRealPropertyUnitAddressSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = LeaseRealPropertyUnit
        fields = ('identification_number', 'name', 'area', 'registry_date', 'addresses')

    def create(self, validated_data):
        addresses = validated_data.pop('addresses', [])

        instance = super().create(validated_data)

        for address in addresses:
            LeaseRealPropertyUnitAddress.objects.create(lease_property_unit=instance, address=address['address'])

        return instance

    def update(self, instance, validated_data):
        addresses = validated_data.pop('addresses', [])

        instance.addresses.all().delete()

        for address in addresses:
            LeaseRealPropertyUnitAddress.objects.create(lease_property_unit=instance, address=address['address'])

        return instance


class LeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    application = ApplicationSerializer(required=False, allow_null=True)
    preparer = UserSerializer(required=False, allow_null=True)
    building_footprints = LeaseBuildingFootprintSerializer(many=True, required=False, allow_null=True)
    decisions = DecisionSerializer(many=True, required=False, allow_null=True)
    real_property_units = LeaseRealPropertyUnitSerializer(many=True, required=False, allow_null=True)
    rents = RentSerializer(many=True, required=False, allow_null=True)
    tenants = TenantSerializer(many=True, required=False, allow_null=True)
    identifier = serializers.ReadOnlyField(source='identifier_string')
    areas = AreaSerializer(many=True, required=False)
    notes = NoteSerializer(many=True, required=False)

    class Meta:
        model = Lease
        fields = '__all__'


class LeaseCreateUpdateSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    application = InstanceDictPrimaryKeyRelatedField(instance_class=Application, queryset=Application.objects.all(),
                                                     required=False, allow_null=True)
    preparer = InstanceDictPrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    building_footprints = LeaseBuildingFootprintSerializer(many=True, required=False, allow_null=True)
    decisions = DecisionSerializer(many=True, required=False, allow_null=True)
    real_property_units = LeaseRealPropertyUnitSerializer(many=True, required=False, allow_null=True)
    rents = RentSerializer(many=True, required=False, allow_null=True)
    tenants = TenantCreateUpdateSerializer(many=True, required=False, allow_null=True)
    identifier = serializers.ReadOnlyField(source='identifier_string')
    areas = AreaSerializer(many=True, required=False, allow_null=True)
    notes = NoteSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Lease
        fields = '__all__'

    def create(self, validated_data):
        building_footprints = validated_data.pop('building_footprints', [])
        decisions = validated_data.pop('decisions', [])
        real_property_units = validated_data.pop('real_property_units', [])
        rents = validated_data.pop('rents', [])
        tenants = validated_data.pop('tenants', [])
        areas = validated_data.pop('areas', [])
        notes = validated_data.pop('notes', [])

        instance = super().create(validated_data)

        instance_replace_related(instance=instance, instance_name='lease', related_name='building_footprints',
                                 serializer_class=LeaseBuildingFootprintSerializer, validated_data=building_footprints)

        instance_replace_related(instance=instance, instance_name='lease', related_name='decisions',
                                 serializer_class=DecisionSerializer, validated_data=decisions)

        instance_replace_related(instance=instance, instance_name='lease', related_name='real_property_units',
                                 serializer_class=LeaseRealPropertyUnitSerializer, validated_data=real_property_units)

        instance_replace_related(instance=instance, instance_name='lease', related_name='rents',
                                 serializer_class=RentSerializer, validated_data=rents)

        instance_replace_related(instance=instance, instance_name='lease', related_name='tenants',
                                 serializer_class=TenantCreateUpdateSerializer, validated_data=tenants)

        instance_replace_related(instance=instance, instance_name='lease', related_name='areas',
                                 serializer_class=AreaSerializer, validated_data=areas)

        instance_replace_related(instance=instance, instance_name='lease', related_name='notes',
                                 serializer_class=NoteSerializer, validated_data=notes)

        instance.create_identifier()

        return instance

    def update(self, instance, validated_data):
        building_footprints = validated_data.pop('building_footprints', None)
        decisions = validated_data.pop('decisions', None)
        real_property_units = validated_data.pop('real_property_units', None)
        rents = validated_data.pop('rents', None)
        tenants = validated_data.pop('tenants', None)
        areas = validated_data.pop('areas', None)
        notes = validated_data.pop('notes', None)

        instance = super().update(instance, validated_data)

        if building_footprints:
            instance_replace_related(instance=instance, related_name='building_footprints',
                                     serializer_class=LeaseBuildingFootprintSerializer,
                                     validated_data=building_footprints)

        if decisions:
            instance_create_or_update_related(instance=instance, instance_name='lease', related_name='decisions',
                                              serializer_class=DecisionSerializer, validated_data=decisions)

        if real_property_units:
            instance_replace_related(instance=instance, instance_name='lease', related_name='real_property_units',
                                     serializer_class=LeaseRealPropertyUnitSerializer,
                                     validated_data=real_property_units)

        if rents:
            instance_create_or_update_related(instance=instance, instance_name='lease', related_name='rents',
                                              serializer_class=RentSerializer,
                                              validated_data=rents)

        if tenants:
            instance_create_or_update_related(instance=instance, instance_name='lease', related_name='tenants',
                                              serializer_class=TenantCreateUpdateSerializer,
                                              validated_data=tenants)

        if areas:
            instance_create_or_update_related(instance=instance, instance_name='lease', related_name='areas',
                                              serializer_class=AreaSerializer,
                                              validated_data=areas)

        if notes:
            instance_create_or_update_related(instance=instance, instance_name='lease', related_name='notes',
                                              serializer_class=NoteSerializer,
                                              validated_data=notes)

        instance.create_identifier()

        return instance
