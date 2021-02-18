from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.models import Contact, DecisionMaker, Plot
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementAttachment,
    LandUseAgreementCondition,
    LandUseAgreementConditionFormOfManagement,
    LandUseAgreementDecision,
    LandUseAgreementDecisionCondition,
    LandUseAgreementDecisionConditionType,
    LandUseAgreementDecisionType,
    LandUseAgreementEstate,
    LandUseAgreementIdentifier,
    LandUseAgreementLitigant,
    LandUseAgreementLitigantContact,
    LandUseAgreementType,
)
from leasing.serializers.decision import DecisionMakerSerializer
from leasing.serializers.land_area import PlotSerializer
from leasing.serializers.lease import (
    ContactSerializer,
    DistrictSerializer,
    MunicipalitySerializer,
)
from users.models import User
from users.serializers import UserSerializer

from .contract import ContractCreateUpdateSerializer, ContractSerializer
from .utils import (
    FileSerializerMixin,
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)


class LandUseAgreementTypeSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementType
        fields = "__all__"


class LandUseAgreementConditionFormOfManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementConditionFormOfManagement
        fields = "__all__"


class LandUseAgreementConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementCondition
        fields = (
            "id",
            "form_of_management",
            "obligated_area",
            "actualized_area",
            "subvention_amount",
            "compensation_pc",
            "supervision_date",
            "supervised_date",
        )


class LandUseAgreementConditionCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    form_of_management = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementConditionFormOfManagement,
        queryset=LandUseAgreementConditionFormOfManagement.objects.all(),
        related_serializer=LandUseAgreementConditionFormOfManagementSerializer,
    )

    class Meta:
        model = LandUseAgreementCondition
        fields = (
            "id",
            "form_of_management",
            "obligated_area",
            "actualized_area",
            "subvention_amount",
            "compensation_pc",
            "supervision_date",
            "supervised_date",
        )


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


class LandUseAgreementAttachmentSerializer(
    FileSerializerMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = LandUseAgreementAttachment
        fields = (
            "id",
            "type",
            "file",
            "filename",
            "uploader",
            "uploaded_at",
            "land_use_agreement",
        )
        download_url_name = "landuseagreementattachment-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class LandUseAgreementAttachmentCreateUpdateSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = LandUseAgreementAttachment
        fields = ("id", "type", "file", "uploader", "uploaded_at", "land_use_agreement")
        read_only_fields = ("uploaded_at",)


class LandUseAgreementDecisionConditionTypeSerializer(NameModelSerializer):
    class Meta:
        model = LandUseAgreementDecisionConditionType
        fields = "__all__"


class LandUseAgreementDecisionConditionSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LandUseAgreementDecisionCondition
        fields = ("id", "type", "supervision_date", "supervised_date", "description")


class LandUseAgreementDecisionConditionCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementDecisionConditionType,
        queryset=LandUseAgreementDecisionConditionType.objects.all(),
        related_serializer=LandUseAgreementDecisionConditionTypeSerializer,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = LandUseAgreementDecisionCondition
        fields = ("id", "type", "supervision_date", "supervised_date", "description")


class LandUseAgreementDecisionTypeSerializer(
    EnumSupportSerializerMixin, NameModelSerializer
):
    class Meta:
        model = LandUseAgreementDecisionType
        fields = "__all__"


class LandUseAgreementDecisionSerializer(
    UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    type = LandUseAgreementDecisionTypeSerializer(required=False, allow_null=True)
    conditions = LandUseAgreementDecisionConditionSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementDecision
        fields = (
            "id",
            "reference_number",
            "decision_maker",
            "decision_date",
            "section",
            "type",
            "conditions",
            "description",
        )


class LandUseAgreementDecisionCreateUpdateNestedSerializer(
    UpdateNestedMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    """This is used when the decision is added or updated inside a land use agreement

    The land use agreement is not included here, but set via the UpdateNestedMixin
    in LandUseAgreementCreateUpdateSerializer.
    """

    id = serializers.IntegerField(required=False)
    type = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementDecisionType,
        queryset=LandUseAgreementDecisionType.objects.all(),
        related_serializer=LandUseAgreementDecisionTypeSerializer,
        required=False,
        allow_null=True,
    )
    conditions = LandUseAgreementDecisionConditionCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
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
            "type",
            "description",
            "conditions",
        )


class LandUseAgreementEstateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.ReadOnlyField()

    class Meta:
        model = LandUseAgreementEstate
        fields = ("id", "estate_id")


class LandUseAgreementEstateCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LandUseAgreementEstate
        fields = ("id", "estate_id")


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
    attachments = None

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


class LandUseAgreementPlotCreateUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Plot
        fields = ("id",)


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
    plots = PlotSerializer(many=True, required=False, allow_null=True)
    attachments = LandUseAgreementAttachmentSerializer(
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
            "plots",
            "attachments",
        )


class LandUseAgreementUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LandUseAgreementIdentifierSerializer(read_only=True)
    decisions = LandUseAgreementDecisionCreateUpdateNestedSerializer(
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
    estate_ids = LandUseAgreementEstateCreateUpdateSerializer(
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
    plots = LandUseAgreementPlotCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    attachments = LandUseAgreementAttachmentSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreement
        fields = "__all__"

    def update(self, instance, validated_data):
        if "plots" in validated_data:
            plots = validated_data.pop("plots")
            plot_ids = []
            for plot_item in plots:
                plot = Plot.objects.get(id=plot_item["id"])
                if plot.is_master:
                    plot.pk = None
                    plot.is_master = False
                    plot.save()
                    instance.plots.add(plot)
                plot_ids.append(plot.id)
            instance.plots.exclude(id__in=plot_ids).delete()
        instance = super().update(instance, validated_data)

        return instance


class LandUseAgreementCreateSerializer(LandUseAgreementUpdateSerializer):
    class Meta:
        model = LandUseAgreement
        fields = "__all__"
