from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import Union
from django.db.models import DurationField, Q
from django.db.models.functions import Cast
from django.utils.translation import ugettext_lazy as _
from enumfields.drf import EnumField, EnumSupportSerializerMixin
from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.enums import LeaseRelationType
from leasing.models import (
    AreaNote,
    BasisOfRent,
    EmailLog,
    InfillDevelopmentCompensation,
    RelatedLease,
    ReservationProcedure,
)
from leasing.serializers.debt_collection import (
    CollectionCourtDecisionSerializer,
    CollectionLetterSerializer,
    CollectionNoteSerializer,
)
from leasing.serializers.invoice import (
    InvoiceNoteCreateUpdateSerializer,
    InvoiceNoteSerializer,
)
from plotsearch.models import (
    AreaSearch,
    PlotSearch,
    RelatedPlotApplication,
    TargetStatus,
)
from users.models import User
from users.serializers import UserSerializer

from ..models import (
    Contact,
    District,
    Financing,
    Hitas,
    IntendedUse,
    Lease,
    LeaseIdentifier,
    LeaseType,
    Municipality,
    NoticePeriod,
    Regulation,
    SpecialProject,
    StatisticalUse,
    SupportiveHousing,
)
from .contact import ContactSerializer
from .contract import ContractCreateUpdateSerializer, ContractSerializer
from .decision import DecisionCreateUpdateNestedSerializer, DecisionSerializer
from .inspection import InspectionSerializer
from .land_area import (
    LeaseAreaCreateUpdateSerializer,
    LeaseAreaListSerializer,
    LeaseAreaSerializer,
    LeaseAreaWithGeometryListSerializer,
)
from .rent import (
    LeaseBasisOfRentCreateUpdateSerializer,
    LeaseBasisOfRentSerializer,
    RentCreateUpdateSerializer,
    RentSerializer,
)
from .tenant import TenantCreateUpdateSerializer, TenantSerializer
from .utils import (
    InstanceDictPrimaryKeyRelatedField,
    NameModelSerializer,
    UpdateNestedMixin,
)


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ("model",)


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = "__all__"


class FinancingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Financing
        fields = "__all__"


class HitasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hitas
        fields = "__all__"


class IntendedUseSerializer(serializers.ModelSerializer):
    class Meta:
        ref_name = "lease_intended_use"
        model = IntendedUse
        fields = "__all__"


class LeaseTypeSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = LeaseType
        fields = "__all__"


class MunicipalitySerializer(NameModelSerializer):
    class Meta:
        model = Municipality
        fields = "__all__"


class NoticePeriodSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = NoticePeriod
        fields = "__all__"


class RegulationSerializer(NameModelSerializer):
    class Meta:
        model = Regulation
        fields = "__all__"


class StatisticalUseSerializer(NameModelSerializer):
    class Meta:
        model = StatisticalUse
        fields = "__all__"


class SupportiveHousingSerializer(NameModelSerializer):
    class Meta:
        model = SupportiveHousing
        fields = "__all__"


class SpecialProjectSerializer(NameModelSerializer):
    class Meta:
        model = SpecialProject
        fields = "__all__"


class ReservationProcedureSerializer(NameModelSerializer):
    class Meta:
        model = ReservationProcedure
        fields = "__all__"


class LeaseIdentifierSerializer(serializers.ModelSerializer):
    type = LeaseTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()

    class Meta:
        model = LeaseIdentifier
        fields = ("type", "municipality", "district", "sequence")


class TargetStatusSuccinctSerializer(serializers.ModelSerializer):
    received_at = serializers.DateTimeField(source="answer.created_at")

    class Meta:
        model = TargetStatus
        fields = (
            "id",
            "application_identifier",
            "received_at",
        )


class PlotSearchSuccinctSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    begin_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    type = serializers.CharField(source="subtype.plot_search_type.name")
    subtype = serializers.CharField(source="subtype.name")

    class Meta:
        model = PlotSearch
        fields = (
            "id",
            "name",
            "begin_at",
            "end_at",
            "type",
            "subtype",
        )


class AreaSearchSuccinctSerializer(serializers.ModelSerializer):
    intended_use = serializers.CharField(source="intended_use.name")
    applicant_first_name = serializers.SerializerMethodField()
    applicant_last_name = serializers.SerializerMethodField()

    def get_applicant_first_name(self, obj):
        user = getattr(obj.answer, "user", None)
        return getattr(user, "first_name", None)

    def get_applicant_last_name(self, obj):
        user = getattr(obj.answer, "user", None)
        return getattr(user, "last_name", None)

    class Meta:
        model = AreaSearch
        fields = (
            "id",
            "identifier",
            "received_date",
            "start_date",
            "end_date",
            "intended_use",
            "applicant_first_name",
            "applicant_last_name",
        )


class LeaseSuccinctSerializer(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = LeaseTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()
    identifier = LeaseIdentifierSerializer(read_only=True)

    class Meta:
        model = Lease
        fields = (
            "id",
            "deleted",
            "created_at",
            "modified_at",
            "type",
            "municipality",
            "district",
            "identifier",
            "start_date",
            "end_date",
            "state",
            "is_rent_info_complete",
            "is_invoicing_enabled",
            "reference_number",
            "note",
            "preparer",
            "is_subject_to_vat",
        )


class RelatedPlotApplicationSerializer(serializers.ModelSerializer):
    content_type = ContentTypeSerializer(read_only=True)
    content_type_id = serializers.IntegerField(write_only=True)
    content_object = serializers.SerializerMethodField()

    def get_content_object(self, obj):
        content_type = obj.content_type
        if content_type.model == "areasearch":
            serializer = AreaSearchSuccinctSerializer(obj.content_object)
        elif content_type.model == "targetstatus":
            serializer = TargetStatusSuccinctSerializer(obj.content_object)
        else:
            return None
        return serializer.data

    class Meta:
        model = RelatedPlotApplication
        fields = (
            "id",
            "lease",
            "content_type",
            "content_object",
            "content_type_id",
        )
        read_only_fields = ("content_object",)


class LeaseSuccinctWithPlotSearchInformationSerializer(LeaseSuccinctSerializer):
    plot_searches = serializers.SerializerMethodField(read_only=True, required=False)
    related_plot_applications = RelatedPlotApplicationSerializer(
        read_only=True, many=True
    )
    target_statuses = TargetStatusSuccinctSerializer(
        read_only=True, many=True, required=False
    )
    area_searches = AreaSearchSuccinctSerializer(
        read_only=True, many=True, required=False
    )

    def get_plot_searches(self, obj: Lease):
        """Return the PlotSearches associated with the Lease via
        PlotSearchTarget->PlanUnit->LeaseArea->Lease, and/or
        PlotSearchTarget->CustomDetailedPlan->LeaseArea->Lease, if any."""
        plot_searches = PlotSearch.objects.filter(
            Q(plot_search_targets__plan_unit__lease_area__lease=obj)
            | Q(plot_search_targets__custom_detailed_plan__lease_area__lease=obj)
        )

        serializer = PlotSearchSuccinctSerializer(plot_searches, many=True)
        return serializer.data

    class Meta:
        model = Lease
        fields = (
            "id",
            "deleted",
            "created_at",
            "modified_at",
            "type",
            "municipality",
            "district",
            "identifier",
            "start_date",
            "end_date",
            "state",
            "is_rent_info_complete",
            "is_invoicing_enabled",
            "reference_number",
            "note",
            "preparer",
            "is_subject_to_vat",
            "target_statuses",
            "plot_searches",
            "area_searches",
            "related_plot_applications",
        )


class LeaseSuccinctWithGeometrySerializer(LeaseSuccinctSerializer):
    lease_areas = LeaseAreaWithGeometryListSerializer(
        many=True, required=False, allow_null=True
    )

    class Meta:
        model = Lease
        fields = (
            "id",
            "deleted",
            "created_at",
            "modified_at",
            "type",
            "municipality",
            "district",
            "identifier",
            "start_date",
            "end_date",
            "state",
            "is_rent_info_complete",
            "is_invoicing_enabled",
            "reference_number",
            "note",
            "preparer",
            "is_subject_to_vat",
            "lease_areas",
        )


class RelatedToLeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    to_lease = LeaseSuccinctWithPlotSearchInformationSerializer()

    class Meta:
        model = RelatedLease
        fields = "__all__"


class RelatedLeaseSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    def validate(self, data):
        if data["from_lease"] == data["to_lease"]:
            raise serializers.ValidationError(
                _("from_lease and to_lease cannot be the same Lease")
            )

        return data

    class Meta:
        model = RelatedLease
        fields = "__all__"


class RelatedFromLeaseSerializer(
    EnumSupportSerializerMixin, serializers.ModelSerializer
):
    from_lease = LeaseSuccinctWithPlotSearchInformationSerializer()

    class Meta:
        model = RelatedLease
        fields = "__all__"


class LeaseSerializerBase(
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    type = LeaseTypeSerializer()
    municipality = MunicipalitySerializer()
    district = DistrictSerializer()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaSerializer(many=True, required=False, allow_null=True)
    lessor = ContactSerializer(required=False, allow_null=True)
    contracts = ContractSerializer(many=True, required=False, allow_null=True)
    decisions = DecisionSerializer(many=True, required=False, allow_null=True)
    inspections = InspectionSerializer(many=True, required=False, allow_null=True)
    rents = RentSerializer(many=True, required=False, allow_null=True)
    basis_of_rents = LeaseBasisOfRentSerializer(
        many=True, required=False, allow_null=True
    )
    collection_court_decisions = CollectionCourtDecisionSerializer(
        many=True, required=False, allow_null=True
    )
    collection_letters = CollectionLetterSerializer(
        many=True, required=False, allow_null=True
    )
    collection_notes = CollectionNoteSerializer(
        many=True, required=False, allow_null=True
    )
    invoice_notes = InvoiceNoteSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Lease
        exclude = ("related_leases",)


class LeaseListSerializer(LeaseSerializerBase):
    basis_of_rents = None
    contracts = None
    decisions = None
    inspections = None
    rents = None
    related_leases = None
    lease_areas = LeaseAreaListSerializer(many=True, required=False, allow_null=True)
    collection_court_decisions = None
    collection_letters = None
    collection_notes = None


def get_related_lease_predecessors(to_lease_id, accumulator=None):
    if accumulator is None:
        accumulator = []

    accumulator.append(to_lease_id)

    result = set()
    predecessors = RelatedLease.objects.filter(to_lease=to_lease_id).select_related(
        "to_lease", "from_lease"
    )

    if predecessors:
        for predecessor in predecessors:
            result.add(predecessor)

            if predecessor.from_lease_id == predecessor.to_lease_id:
                continue

            if predecessor.from_lease_id in accumulator:
                continue

            result.update(
                get_related_lease_predecessors(predecessor.from_lease_id, accumulator)
            )

    return result


def get_related_leases(obj):
    # Immediate successors
    related_to_leases = set(
        RelatedLease.objects.filter(from_lease=obj).select_related(
            "to_lease", "from_lease"
        )
    )
    # All predecessors
    related_from_leases = get_related_lease_predecessors(obj.id)

    return {
        "related_to": RelatedToLeaseSerializer(related_to_leases, many=True).data,
        "related_from": RelatedFromLeaseSerializer(related_from_leases, many=True).data,
    }


class LeaseRetrieveSerializer(LeaseSerializerBase):
    related_leases = serializers.SerializerMethodField()
    related_plot_applications = RelatedPlotApplicationSerializer(
        read_only=True, many=True
    )
    target_statuses = TargetStatusSuccinctSerializer(
        read_only=True, many=True, required=False
    )
    plot_searches = serializers.SerializerMethodField(read_only=True, required=False)
    area_searches = AreaSearchSuccinctSerializer(
        read_only=True, many=True, required=False
    )
    preparer = UserSerializer()
    infill_development_compensations = serializers.SerializerMethodField()
    email_logs = serializers.SerializerMethodField()
    area_notes = serializers.SerializerMethodField()
    matching_basis_of_rents = serializers.SerializerMethodField()

    def get_related_leases(self, obj):
        return get_related_leases(obj)

    def get_plot_searches(self, obj: Lease):
        return LeaseSuccinctWithPlotSearchInformationSerializer.get_plot_searches(
            self, obj
        )

    def override_permission_check_field_name(self, field_name):
        if field_name == "infill_development_compensations":
            return "infill_development_compensation_leases"

        if field_name in ("area_notes", "email_logs"):
            return "lease_areas"

        return field_name

    def get_infill_development_compensations(self, obj):
        infill_development_compensations = InfillDevelopmentCompensation.objects.filter(
            infill_development_compensation_leases__lease__id=obj.id
        )

        return [
            {"id": idc.id, "name": idc.name} for idc in infill_development_compensations
        ]

    def get_email_logs(self, obj):
        from leasing.serializers.email import EmailLogSerializer

        lease_content_type = ContentType.objects.get_for_model(obj)
        email_logs = EmailLog.objects.filter(
            content_type=lease_content_type, object_id=obj.id
        )

        return EmailLogSerializer(email_logs, many=True).data

    def get_area_notes(self, obj):
        from leasing.serializers.area_note import AreaNoteSerializer

        area_notes = None
        combined_area = obj.lease_areas.aggregate(union=Union("geometry"))["union"]
        if combined_area:
            area_notes = AreaNote.objects.filter(geometry__intersects=combined_area)

        return AreaNoteSerializer(area_notes, many=True).data

    def get_matching_basis_of_rents(self, obj):
        from leasing.serializers.basis_of_rent import BasisOfRentSerializer

        q = Q()
        property_identifiers = obj.lease_areas.values_list("identifier", flat=True)
        if property_identifiers:
            q = Q(property_identifiers__identifier__in=property_identifiers)

        combined_area = obj.lease_areas.aggregate(union=Union("geometry"))["union"]
        if combined_area:
            q |= Q(geometry__intersects=combined_area)

        if not q:
            return []

        return BasisOfRentSerializer(BasisOfRent.objects.filter(q), many=True).data

    class Meta:
        model = Lease
        fields = "__all__"
        exclude = None


class LeaseUpdateSerializer(
    UpdateNestedMixin,
    EnumSupportSerializerMixin,
    FieldPermissionsSerializerMixin,
    serializers.ModelSerializer,
):
    id = serializers.ReadOnlyField()
    identifier = LeaseIdentifierSerializer(read_only=True)
    tenants = TenantCreateUpdateSerializer(many=True, required=False, allow_null=True)
    lease_areas = LeaseAreaCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    lessor = InstanceDictPrimaryKeyRelatedField(
        instance_class=Contact,
        queryset=Contact.objects.filter(is_lessor=True),
        related_serializer=ContactSerializer,
        required=False,
        allow_null=True,
    )
    contracts = ContractCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    decisions = DecisionCreateUpdateNestedSerializer(
        many=True, required=False, allow_null=True
    )
    inspections = InspectionSerializer(many=True, required=False, allow_null=True)
    rents = RentCreateUpdateSerializer(many=True, required=False, allow_null=True)
    basis_of_rents = LeaseBasisOfRentCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )
    preparer = InstanceDictPrimaryKeyRelatedField(
        instance_class=User,
        queryset=User.objects.all(),
        related_serializer=UserSerializer,
        required=False,
        allow_null=True,
    )
    related_leases = serializers.SerializerMethodField()
    notice_period = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=NoticePeriod.objects.all()
        .annotate(duration_as_interval=Cast("duration", DurationField()))
        .order_by("duration_as_interval"),
    )
    invoice_notes = InvoiceNoteCreateUpdateSerializer(
        many=True, required=False, allow_null=True
    )

    def get_related_leases(self, obj):
        return get_related_leases(obj)

    class Meta:
        model = Lease
        fields = "__all__"
        read_only_fields = ("is_invoicing_enabled", "is_rent_info_complete")


class LeaseCreateSerializer(LeaseUpdateSerializer):
    relate_to = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True, queryset=Lease.objects.all()
    )
    relation_type = EnumField(required=False, allow_null=True, enum=LeaseRelationType)

    def override_permission_check_field_name(self, field_name):
        if field_name in ("relate_to", "relation_type"):
            return "related_leases"

        return field_name

    class Meta:
        model = Lease
        fields = "__all__"
        read_only_fields = ("is_invoicing_enabled", "is_rent_info_complete")
