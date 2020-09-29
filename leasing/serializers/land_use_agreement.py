from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementDecision,
    LandUseAgreementEstate,
    LandUseAgreementIdentifier,
    LandUseAgreementType,
)
from leasing.serializers.decision import (
    DecisionCreateUpdateNestedSerializer,
    DecisionMakerSerializer,
)
from leasing.serializers.lease import DistrictSerializer, MunicipalitySerializer
from users.models import User
from users.serializers import UserSerializer

from .contract import ContractSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class LandUseAgreementTypeSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementType
        fields = "__all__"


class LandUseAgreementIdentifierSerializer(serializers.ModelSerializer):
    type = LandUseAgreementTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()

    class Meta:
        model = LandUseAgreementIdentifier
        fields = ("type", "municipality", "district", "sequence")


class LandUseAgreementAddressSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()

    class Meta:
        model = LandUseAgreementAddress
        fields = ("id", "address", "postal_code", "city", "is_primary")


class LandUseAgreementDecisionSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LandUseAgreementDecision
        fields = (
            "id",
            "reference_number",
            "decision_maker",
            "decision_date",
            "section",
        )


class LandUseAgreementEstateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementEstate
        fields = ("estate_id",)


class LandUseAgreementListSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = LandUseAgreementTypeSerializer()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    contracts = ContractSerializer(many=True, required=False, allow_null=True)
    decisions = LandUseAgreementDecisionSerializer(
        many=True, required=False, allow_null=True
    )
    estate_ids = LandUseAgreementEstateSerializer(
        many=True, required=False, allow_null=True
    )
    addresses = LandUseAgreementAddressSerializer(many=True)

    class Meta:
        model = LandUseAgreement
        fields = "__all__"


class LandUseAgreementRetrieveSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    preparer = UserSerializer()
    plan_acceptor = DecisionMakerSerializer()
    addresses = LandUseAgreementAddressSerializer(
        many=True, required=False, allow_null=True
    )
    contracts = ContractSerializer(many=True, required=False, allow_null=True)
    decisions = LandUseAgreementDecisionSerializer(many=True)
    estate_ids = LandUseAgreementEstateSerializer(many=True)

    class Meta:
        model = LandUseAgreement
        fields = (
            "id",
            "identifier",
            "preparer",
            "addresses",
            "contracts",
            "type",
            "estimated_completion_year",
            "estimated_introduction_year",
            "project_area",
            "plan_reference_number",
            "plan_number",
            "plan_acceptor",
            "plan_lawfulness_date",
            "state",
            "land_use_contract_type",
            "decisions",
            "estate_ids",
            "definition",
            "status",
        )


class LandUseAgreementUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    decisions = DecisionCreateUpdateNestedSerializer(
        many=True, required=False, allow_null=True
    )
    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )
    estate_ids = LandUseAgreementEstateSerializer(
        many=True, required=False, allow_null=True
    )
    addresses = LandUseAgreementAddressSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreement
        fields = "__all__"


class LandUseAgreementCreateSerializer(LandUseAgreementUpdateSerializer):
    class Meta:
        model = LandUseAgreement
        fields = "__all__"
