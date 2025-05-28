from django.contrib.auth.models import Group
from django.db.models import QuerySet
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models.contract import Collateral, CollateralType
from users.models import User
from users.serializers import UserSerializer

from ..models import Contract, ContractChange, ContractType, Decision
from .decision import DecisionSerializer
from .utils import (
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)


def get_users_for_executor_field() -> QuerySet[User]:
    """
    Returns a queryset of users that can be assigned as executors
    for contracts or contract changes.
    """

    executor_auth_group_names = [
        "Valmistelija",
        "Syöttäjä",
        "Sopimusvalmistelija",
    ]
    auth_group_ids = Group.objects.filter(
        name__in=executor_auth_group_names
    ).values_list("id", flat=True)
    users = (
        User.objects.filter(is_active=True, groups__id__in=auth_group_ids)
        .distinct()
        .order_by("last_name", "first_name", "username")
    )

    if not users.exists():
        return User.objects.none()

    return users


class ContractChangeSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    executor = UserSerializer()

    class Meta:
        model = ContractChange
        fields = (
            "id",
            "signing_date",
            "sign_by_date",
            "first_call_sent",
            "second_call_sent",
            "third_call_sent",
            "description",
            "decision",
            "executor",
        )


class ContractChangeCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    decision = InstanceDictPrimaryKeyRelatedField(
        instance_class=Decision,
        queryset=Decision.objects.all(),
        related_serializer=DecisionSerializer,
        required=False,
        allow_null=True,
    )
    executor = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=get_users_for_executor_field(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ContractChange
        fields = (
            "id",
            "signing_date",
            "sign_by_date",
            "first_call_sent",
            "second_call_sent",
            "third_call_sent",
            "description",
            "decision",
            "executor",
        )


class CollateralTypeSerializer(NameModelSerializer):
    class Meta:
        model = CollateralType
        fields = "__all__"


class CollateralSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Collateral
        exclude = ("contract",)


class CollateralCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=CollateralType,
        queryset=CollateralType.objects.all(),
        related_serializer=CollateralTypeSerializer,
    )

    class Meta:
        model = Collateral
        exclude = ("contract",)


class ContractTypeSerializer(NameModelSerializer):
    class Meta:
        model = ContractType
        fields = "__all__"


class ContractSerializer(FieldPermissionsSerializerMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    contract_changes = ContractChangeSerializer(
        many=True, required=False, allow_null=True
    )
    collaterals = CollateralSerializer(many=True, required=False, allow_null=True)
    executor = UserSerializer()

    class Meta:
        model = Contract
        fields = (
            "id",
            "type",
            "contract_number",
            "signing_date",
            "sign_by_date",
            "signing_note",
            "is_readjustment_decision",
            "decision",
            "ktj_link",
            "institution_identifier",
            "first_call_sent",
            "second_call_sent",
            "third_call_sent",
            "contract_changes",
            "collaterals",
            "executor",
        )
        read_only_fields = ("is_readjustment_decision",)


class ContractCreateUpdateSerializer(
    UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=ContractType,
        queryset=ContractType.objects.all(),
        related_serializer=ContractTypeSerializer,
    )
    decision = InstanceDictPrimaryKeyRelatedField(
        instance_class=Decision,
        queryset=Decision.objects.all(),
        related_serializer=DecisionSerializer,
        required=False,
        allow_null=True,
    )
    contract_changes = ContractChangeCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    collaterals = CollateralCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    executor = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=get_users_for_executor_field(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Contract
        fields = (
            "id",
            "type",
            "contract_number",
            "signing_date",
            "sign_by_date",
            "signing_note",
            "is_readjustment_decision",
            "decision",
            "ktj_link",
            "institution_identifier",
            "first_call_sent",
            "second_call_sent",
            "third_call_sent",
            "contract_changes",
            "collaterals",
            "executor",
        )
        read_only_fields = ("is_readjustment_decision",)
