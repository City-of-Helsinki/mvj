from django.utils.translation import gettext as _
from django_countries.serializers import CountryFieldMixin
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin

from ..models import Contact, ServiceUnit
from .service_unit import ServiceUnitSerializer
from .utils import InstanceDictPrimaryKeyRelatedField


class ContactSerializer(
    EnumSupportSerializerMixin,
    CountryFieldMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    service_unit = ServiceUnitSerializer(read_only=True)

    class Meta:
        model = Contact
        fields = "__all__"

    def get_contacts_active_leases(self, contact: Contact):
        return contact.get_contacts_active_leases()


class ContactSerializerWithActiveLeases(ContactSerializer):
    contacts_active_leases = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ("contacts_active_leases",)


class ContactCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    CountryFieldMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    service_unit = InstanceDictPrimaryKeyRelatedField(
        instance_class=ServiceUnit,
        queryset=ServiceUnit.objects.all(),
        related_serializer=ServiceUnitSerializer,
        required=True,
    )
    contacts_active_leases = serializers.SerializerMethodField()

    def get_contacts_active_leases(self, contact: Contact):
        return contact.get_contacts_active_leases()

    def validate_service_unit(self, value):
        request = self.context.get("request")
        if not request or request.user.is_superuser:
            return value

        # TODO: Should the users in an admin group have the permission to change service unit?
        if self.context.get("view").action == "create":
            if value not in request.user.service_units.all():
                raise serializers.ValidationError(
                    _("Can only add contacts to service units the user is a member of")
                )
        else:
            if value != self.instance.service_unit:
                raise serializers.ValidationError(_("Cannot change service unit"))

        return value

    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ("contacts_active_leases",)
