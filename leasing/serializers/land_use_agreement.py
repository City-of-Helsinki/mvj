from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import Contact, DecisionMaker
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementCondition,
    LandUseAgreementConditionType,
    LandUseAgreementDecision,
    LandUseAgreementEstate,
    LandUseAgreementIdentifier,
    LandUseAgreementLitigant,
    LandUseAgreementLitigantContact,
    LandUseAgreementType,
)
from leasing.serializers.decision import DecisionMakerSerializer
from leasing.serializers.lease import (
    ContactSerializer,
    DistrictSerializer,
    MunicipalitySerializer,
)
from users.models import User
from users.serializers import UserSerializer

from .contract import ContractCreateUpdateSerializer, ContractSerializer
from .utils import InstanceDictPrimaryKeyRelatedField, UpdateNestedMixin


class LandUseAgreementTypeSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementType
        fields = "__all__"


class LandUseAgreementConditionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementConditionType
        fields = "__all__"


class LandUseAgreementConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementCondition
        fields = ("id", "type", "supervision_date", "supervised_date", "description")


class LandUseAgreementConditionCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementConditionType,
        queryset=LandUseAgreementConditionType.objects.all(),
        related_serializer=LandUseAgreementConditionTypeSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LandUseAgreementCondition
        fields = ("id", "type", "supervision_date", "supervised_date", "description")


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
    UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    decision_maker = InstanceDictPrimaryKeyRelatedField(
        instance_class=DecisionMaker,
        queryset=DecisionMaker.objects.all(),
        related_serializer=DecisionMakerSerializer,
        required=False,
        allow_null=True,
    )

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


class LandUseAgreementLitigantContactSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    contact = ContactSerializer()

    class Meta:
        model = LandUseAgreementLitigantContact
        fields = ("id", "type", "contact", "start_date", "end_date")


class LandUseAgreementLitigantContactCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    contact = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
    )

    class Meta:
        model = LandUseAgreementLitigantContact
        fields = ("id", "type", "contact", "start_date", "end_date")


class LandUseAgreementLitigantSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    landuseagreementlitigantcontact_set = LandUseAgreementLitigantContactSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementLitigant
        fields = (
            "id",
            "share_numerator",
            "share_denominator",
            "reference",
            "landuseagreementlitigantcontact_set",
        )


class LandUseAgreementLitigantCreateUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    landuseagreementlitigantcontact_set = LandUseAgreementLitigantContactCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementLitigant
        fields = (
            "id",
            "share_numerator",
            "share_denominator",
            "reference",
            "landuseagreementlitigantcontact_set",
        )


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
    litigants = LandUseAgreementLitigantSerializer(
        many=True, required=False, allow_null=True
    )

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
            "litigants",
            "conditions",
        )


class LandUseAgreementRetrieveSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    preparer = UserSerializer()
    addresses = LandUseAgreementAddressSerializer(
        many=True, required=False, allow_null=True
    )
    contracts = ContractSerializer(many=True, required=False, allow_null=True)
    decisions = LandUseAgreementDecisionSerializer(many=True)
    estate_ids = LandUseAgreementEstateSerializer(many=True)
    litigants = LandUseAgreementLitigantSerializer(
        many=True, required=False, allow_null=True
    )
    conditions = LandUseAgreementConditionSerializer(
        many=True, required=False, allow_null=True
    )

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
            "litigants",
            "conditions",
        )


class LandUseAgreementUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    decisions = LandUseAgreementDecisionSerializer(
        many=True, required=False, allow_null=True
    )
    contracts = ContractCreateUpdateSerializer(
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
    litigants = LandUseAgreementLitigantCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    conditions = LandUseAgreementConditionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreement
        fields = "__all__"


class LandUseAgreementCreateSerializer(LandUseAgreementUpdateSerializer):
    class Meta:
        model = LandUseAgreement
        fields = "__all__"
