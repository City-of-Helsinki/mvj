from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.fields import empty

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import InvoiceState, InvoiceType
from leasing.models import Contact, DecisionMaker, Plot
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementAttachment,
    LandUseAgreementCompensations,
    LandUseAgreementCompensationsUnitPrice,
    LandUseAgreementCondition,
    LandUseAgreementConditionFormOfManagement,
    LandUseAgreementDecision,
    LandUseAgreementDecisionCondition,
    LandUseAgreementDecisionConditionType,
    LandUseAgreementDecisionType,
    LandUseAgreementEstate,
    LandUseAgreementIdentifier,
    LandUseAgreementInvoice,
    LandUseAgreementInvoicePayment,
    LandUseAgreementInvoiceRow,
    LandUseAgreementInvoiceSet,
    LandUseAgreementLitigant,
    LandUseAgreementLitigantContact,
    LandUseAgreementReceivableType,
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


class LandUseAgreementConditionFormOfManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementConditionFormOfManagement
        fields = "__all__"


class LandUseAgreementTypeSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementType
        fields = "__all__"


class LandUseAgreementCompensationsUnitPriceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LandUseAgreementCompensationsUnitPrice
        fields = (
            "id",
            "usage",
            "management",
            "protected",
            "area",
            "unit_value",
            "discount",
            "used_price",
        )


class LandUseAgreementCompensationsUnitPriceCreateUpdateSerializer(
    serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    management = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementConditionFormOfManagement,
        queryset=LandUseAgreementConditionFormOfManagement.objects.all(),
        related_serializer=LandUseAgreementConditionFormOfManagementSerializer,
    )

    class Meta:
        model = LandUseAgreementCompensationsUnitPrice
        fields = (
            "id",
            "usage",
            "management",
            "protected",
            "area",
            "unit_value",
            "discount",
            "used_price",
        )


class LandUseAgreementCompensationsSerializer(serializers.ModelSerializer):
    unit_prices_used_in_calculation = LandUseAgreementCompensationsUnitPriceSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementCompensations
        fields = (
            "id",
            "cash_compensation",
            "land_compensation",
            "other_compensation",
            "first_installment_increase",
            "park_acquisition_value",
            "street_acquisition_value",
            "other_acquisition_value",
            "park_area",
            "street_area",
            "other_area",
            "unit_prices_used_in_calculation",
        )


class LandUseAgreementCompensationsCreateUpdateSerializer(serializers.ModelSerializer):
    unit_prices_used_in_calculation = LandUseAgreementCompensationsUnitPriceCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementCompensations
        fields = (
            "id",
            "cash_compensation",
            "land_compensation",
            "other_compensation",
            "first_installment_increase",
            "park_acquisition_value",
            "street_acquisition_value",
            "other_acquisition_value",
            "park_area",
            "street_area",
            "other_area",
            "unit_prices_used_in_calculation",
        )


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
    compensations = LandUseAgreementCompensationsSerializer(
        required=False, allow_null=True
    )
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
            "compensations",
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
    compensations = LandUseAgreementCompensationsSerializer(
        required=False, allow_null=True
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
            "compensations",
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
    compensations = LandUseAgreementCompensationsCreateUpdateSerializer(
        required=False, allow_null=True
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

        if "compensations" in validated_data:
            compensations_data = validated_data.pop("compensations")
            if compensations_data:
                instance.update_compensations(compensations_data)

        instance = super().update(instance, validated_data)

        return instance


class LandUseAgreementReceivableTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementReceivableType
        fields = "__all__"


class LandUseAgreementCreateSerializer(LandUseAgreementUpdateSerializer):
    class Meta:
        model = LandUseAgreement
        fields = "__all__"


class LandUseAgreementInvoiceRowCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    litigant = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementLitigant,
        queryset=LandUseAgreementLitigant.objects.all(),
        related_serializer=LandUseAgreementLitigantSerializer,
        required=False,
        allow_null=True,
    )
    receivable_type = InstanceDictPrimaryKeyRelatedField(
        instance_class=LandUseAgreementReceivableType,
        queryset=LandUseAgreementReceivableType.objects.all(),
        related_serializer=LandUseAgreementReceivableTypeSerializer,
    )

    class Meta:
        model = LandUseAgreementInvoiceRow
        fields = (
            "id",
            "description",
            "compensation_amount",
            "increase_percentage",
            "litigant",
            "plan_lawfulness_date",
            "receivable_type",
            "sign_date",
            "amount",
        )

    def create(self, validated_data):
        invoice_row = super().create(validated_data)

        invoice_row.update_amount()

        return invoice_row

    def validate(self, data):
        """Validate that rows with an inactive receivable type cannot be created

        Saving an existing row should succeed, but creating
        new rows or changing a rows receivable type to an inactive type
        should fail."""

        valid = True

        if not data["receivable_type"].is_active:
            if self.instance:
                if self.instance.receivable_type != data["receivable_type"]:
                    # We have an existing row but the receivable type wasn't the
                    # same as before
                    valid = False
            else:
                # We have data without an instance.
                # If there is no id it's a new row.
                if "id" not in data:
                    valid = False
                else:
                    # Else try to see if the existing row has the same receivable type
                    try:
                        existing_row = LandUseAgreementInvoiceRow.objects.get(
                            pk=data["id"]
                        )

                        if existing_row.receivable_type != data["receivable_type"]:
                            valid = False
                    except ObjectDoesNotExist:
                        valid = False

        if not valid:
            raise ValidationError(_("Cannot use an inactive receivable type"))

        return data


class LandUseAgreementInvoicePaymentCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LandUseAgreementInvoicePayment
        exclude = ("invoice", "deleted")


class LandUseAgreementInvoiceCreateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
        required=False,
    )
    rows = LandUseAgreementInvoiceRowCreateUpdateSerializer(many=True)
    payments = LandUseAgreementInvoicePaymentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    # Make total_amount, billed_amount, and type not required in the serializer and set them in create() if needed
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    billed_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    type = EnumField(enum=InvoiceType, required=False)

    def override_permission_check_field_name(self, field_name):
        # if field_name == "tenant":
        #    return "recipient"

        return field_name

    def validate(self, attrs):
        if not bool(attrs.get("recipient")) ^ bool(attrs.get("tenant")):
            raise ValidationError(_("Either recipient or tenant is required."))

        if (
            attrs.get("tenant")
            and attrs.get("tenant") not in attrs.get("lease").tenants.all()
        ):
            raise ValidationError(_("Tenant not found in lease"))

        return attrs

    def create(self, validated_data):
        validated_data["state"] = InvoiceState.OPEN

        if not validated_data.get("total_amount"):
            total_amount = Decimal(0)
            for row in validated_data.get("rows", []):
                total_amount += row.get("amount", Decimal(0))

            validated_data["total_amount"] = total_amount

        if not validated_data.get("billed_amount"):
            billed_amount = Decimal(0)
            for row in validated_data.get("rows", []):
                billed_amount += row.get("amount", Decimal(0))

            validated_data["billed_amount"] = billed_amount

        if not validated_data.get("type"):
            validated_data["type"] = InvoiceType.CHARGE

        # if validated_data.get("tenant"):
        #    today = datetime.date.today()
        #    tenant = validated_data.pop("tenant")
        #    billing_tenantcontact = tenant.get_billing_tenantcontacts(
        #        start_date=today, end_date=None
        #    ).first()
        #    if not billing_tenantcontact:
        #        raise ValidationError(_("Billing contact not found for tenant"))

        #    validated_data["recipient"] = billing_tenantcontact.contact
        #    for row in validated_data.get("rows", []):
        #        row["tenant"] = tenant

        invoice = super().create(validated_data)

        invoice.invoicing_date = timezone.now().date()
        invoice.outstanding_amount = validated_data["total_amount"]
        invoice.update_amounts()  # 0€ invoice would stay OPEN otherwise

        return invoice

    class Meta:
        model = LandUseAgreementInvoice
        exclude = ("deleted",)
        read_only_fields = (
            "number",
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "credit_invoices",
            "interest_invoices",
        )


class LandUseAgreementInvoiceUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    recipient = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.all(),
        related_serializer=ContactSerializer,
    )
    rows = LandUseAgreementInvoiceRowCreateUpdateSerializer(many=True)
    payments = LandUseAgreementInvoicePaymentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.refresh_from_db()
        instance.update_amounts()
        if instance.credited_invoice:
            instance.credited_invoice.update_amounts()

        return instance

    class Meta:
        model = LandUseAgreementInvoice
        exclude = ("deleted",)
        read_only_fields = (
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "credit_invoices",
            "interest_invoices",
        )


class LandUseAgreementCreditNoteUpdateSerializer(
    LandUseAgreementInvoiceUpdateSerializer
):
    class Meta:
        model = LandUseAgreementInvoice
        exclude = ("deleted",)
        read_only_fields = (
            "sent_to_sap_at",
            "sap_id",
            "state",
            "adjusted_due_date",
            "due_date",
        )


class SentToSapLandUseAgreementInvoiceUpdateSerializer(
    LandUseAgreementInvoiceUpdateSerializer
):
    """Invoice serializer where all but "postpone_date" is read only"""

    rows = LandUseAgreementInvoiceRowCreateUpdateSerializer(many=True, read_only=True)
    payments = LandUseAgreementInvoicePaymentCreateUpdateSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = LandUseAgreementInvoice
        exclude = ("deleted",)
        read_only_fields = (
            "lease",
            "invoiceset",
            "number",
            "recipient",
            "sent_to_sap_at",
            "sap_id",
            "adjusted_due_date",
            "due_date",
            "invoicing_date",
            "state",
            "total_amount",
            "billed_amount",
            "outstanding_amount",
            "payment_notification_date",
            "collection_charge",
            "payment_notification_catalog_date",
            "delivery_method",
            "type",
            "notes",
            "description",
            "credited_invoices",
            "interest_invoices",
            "rows",
            "payments",
        )


class LandUseAgreementInvoicePaymentSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = LandUseAgreementInvoicePayment
        exclude = ("deleted",)


class LandUseAgreementInvoiceRowSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    litigant = LandUseAgreementLitigantSerializer()

    class Meta:
        model = LandUseAgreementInvoiceRow
        fields = (
            "id",
            "description",
            "compensation_amount",
            "increase_percentage",
            "litigant",
            "plan_lawfulness_date",
            "receivable_type",
            "sign_date",
        )


class LandUseAgreementInlineInvoiceSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    class Meta:
        model = LandUseAgreementInvoice
        fields = ("id", "number", "due_date", "total_amount")


class LandUseAgreementInvoiceSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    recipient = ContactSerializer()
    rows = LandUseAgreementInvoiceRowSerializer(
        many=True, required=False, allow_null=True
    )
    payments = LandUseAgreementInvoicePaymentSerializer(
        many=True, required=False, allow_null=True
    )
    credit_invoices = LandUseAgreementInlineInvoiceSerializer(
        many=True, required=False, allow_null=True
    )
    interest_invoices = LandUseAgreementInlineInvoiceSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = LandUseAgreementInvoice
        exclude = ("deleted",)


class LandUseAgreementInvoiceSerializerWithSuccinctLease(
    LandUseAgreementInvoiceSerializer
):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)

        # Lease field must be added dynamically to prevent circular imports
        from leasing.serializers.lease import LeaseSuccinctSerializer

        self.fields["lease"] = LeaseSuccinctSerializer()


class LandUseAgreementInvoiceSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandUseAgreementInvoiceSet
        fields = (
            "id",
            "land_use_agreement",
            "invoices",
        )
