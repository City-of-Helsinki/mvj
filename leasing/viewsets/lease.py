import datetime
import re

from dateutil.parser import parse, parserinfo
from django.db.models import DurationField, Q
from django.db.models.functions import Cast
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.filters import DistrictFilter, LeaseFilter
from leasing.forms import LeaseSearchForm
from leasing.models import (
    District,
    Financing,
    Hitas,
    IntendedUse,
    Lease,
    LeaseType,
    Management,
    Municipality,
    NoticePeriod,
    Regulation,
    RelatedLease,
    ReservationProcedure,
    SpecialProject,
    StatisticalUse,
    SupportiveHousing,
)
from leasing.models.utils import normalize_property_identifier
from leasing.serializers.common import ManagementSerializer
from leasing.serializers.lease import (
    DistrictSerializer,
    FinancingSerializer,
    HitasSerializer,
    IntendedUseSerializer,
    LeaseCreateSerializer,
    LeaseListSerializer,
    LeaseRetrieveSerializer,
    LeaseSuccinctSerializer,
    LeaseSuccinctWithGeometrySerializer,
    LeaseTypeSerializer,
    LeaseUpdateSerializer,
    MunicipalitySerializer,
    NoticePeriodSerializer,
    RegulationSerializer,
    RelatedLeaseSerializer,
    ReservationProcedureSerializer,
    SpecialProjectSerializer,
    StatisticalUseSerializer,
    SupportiveHousingSerializer,
)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class DistrictViewSet(AtomicTransactionModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    filterset_class = DistrictFilter


class FinancingViewSet(AtomicTransactionModelViewSet):
    queryset = Financing.objects.all()
    serializer_class = FinancingSerializer


class HitasViewSet(AtomicTransactionModelViewSet):
    queryset = Hitas.objects.all()
    serializer_class = HitasSerializer


class IntendedUseViewSet(AtomicTransactionModelViewSet):
    queryset = IntendedUse.objects.all()
    serializer_class = IntendedUseSerializer


class LeaseTypeViewSet(AtomicTransactionModelViewSet):
    queryset = LeaseType.objects.all()
    serializer_class = LeaseTypeSerializer


class ManagementViewSet(AtomicTransactionModelViewSet):
    queryset = Management.objects.all()
    serializer_class = ManagementSerializer


class MunicipalityViewSet(AtomicTransactionModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer


class NoticePeriodViewSet(AtomicTransactionModelViewSet):
    queryset = (
        NoticePeriod.objects.all()
        .annotate(duration_as_interval=Cast("duration", DurationField()))
        .order_by("duration_as_interval")
    )
    serializer_class = NoticePeriodSerializer


class RegulationViewSet(AtomicTransactionModelViewSet):
    queryset = Regulation.objects.all()
    serializer_class = RegulationSerializer


class StatisticalUseViewSet(AtomicTransactionModelViewSet):
    queryset = StatisticalUse.objects.all()
    serializer_class = StatisticalUseSerializer


class SupportiveHousingViewSet(AtomicTransactionModelViewSet):
    queryset = SupportiveHousing.objects.all()
    serializer_class = SupportiveHousingSerializer


class SpecialProjectViewSet(AtomicTransactionModelViewSet):
    queryset = SpecialProject.objects.all()
    serializer_class = SpecialProjectSerializer


class ReservationProcedureViewSet(AtomicTransactionModelViewSet):
    queryset = ReservationProcedure.objects.all()
    serializer_class = ReservationProcedureSerializer


class RelatedLeaseViewSet(AtomicTransactionModelViewSet):
    queryset = RelatedLease.objects.all()
    serializer_class = RelatedLeaseSerializer


class LeaseViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    serializer_class = LeaseRetrieveSerializer
    filterset_class = LeaseFilter
    filter_backends = (DjangoFilterBackend, OrderingFilter, InBBoxFilter)
    ordering = (
        "identifier__type__identifier",
        "identifier__municipality__identifier",
        "identifier__district__identifier",
        "identifier__sequence",
    )
    ordering_fields = (
        "identifier__type__identifier",
        "identifier__municipality__identifier",
        "identifier__district__identifier",
        "identifier__sequence",
        "lessor__name",
        "state",
        "start_date",
        "end_date",
    )
    bbox_filter_field = "lease_areas__geometry"
    bbox_filter_include_overlapping = True

    def get_queryset(self):  # noqa: C901
        """Allow filtering leases by various query parameters

        `identifier` query parameter can be used to find the Lease with the provided identifier.
        example: .../lease/?identifier=S0120-219
        `search` query parameter can be used to find leases by identifier and multiple other fields
        """
        succinct = self.request.query_params.get("succinct")

        if succinct:
            queryset = Lease.objects.succinct_select_related_and_prefetch_related()
        else:
            queryset = Lease.objects.full_select_related_and_prefetch_related()

        if self.action != "list":
            return queryset

        # Simple search
        identifier = self.request.query_params.get("identifier")
        search = self.request.query_params.get("search")

        if identifier is not None or search is not None:
            if search is None:
                search_string = identifier.strip()
                search_by_other = False
            else:
                search_string = search.strip()
                search_by_other = True

            looks_like_identifier = bool(
                re.match(r"[A-Z]+\d{3,4}-\d+$", search_string, re.IGNORECASE)
            )

            # Search by identifier or parts of it
            if len(search_string) < 3:
                identifier_q = Q(
                    identifier__type__identifier__istartswith=search_string
                )
            elif len(search_string) == 3:
                identifier_q = Q(
                    identifier__type__identifier__iexact=search_string[:2],
                    identifier__municipality__identifier=search_string[2:3],
                )
            elif len(search_string) < 7:
                district_identifier = search_string[3:5]
                if district_identifier == "0":
                    identifier_q = Q(
                        identifier__type__identifier__iexact=search_string[:2],
                        identifier__municipality__identifier=search_string[2:3],
                        identifier__district__identifier__in=range(0, 10),
                    )
                else:
                    if district_identifier == "00":
                        district_identifier = "0"
                    else:
                        district_identifier = district_identifier.lstrip("0")

                    identifier_q = Q(
                        identifier__type__identifier__iexact=search_string[:2],
                        identifier__municipality__identifier=search_string[2:3],
                        identifier__district__identifier__startswith=district_identifier,
                    )
            elif looks_like_identifier:
                district_identifier = search_string[3:5]
                if district_identifier == "00":
                    district_identifier = "0"
                else:
                    district_identifier = district_identifier.lstrip("0")

                identifier_q = Q(
                    identifier__type__identifier__iexact=search_string[:2],
                    identifier__municipality__identifier=search_string[2:3],
                    identifier__district__identifier=district_identifier,
                    identifier__sequence__startswith=search_string[6:],
                )
            else:
                identifier_q = Q()

            other_q = Q()

            # Search also by other fields if the search string is clearly not a lease identifier
            if search_by_other and not looks_like_identifier:
                # Address
                other_q |= Q(lease_areas__addresses__address__icontains=search_string)

                # Property identifier
                other_q |= Q(lease_areas__identifier__icontains=search_string)
                normalized_identifier = normalize_property_identifier(search_string)
                if search_string != normalized_identifier:
                    other_q |= Q(
                        lease_areas__identifier__icontains=normalized_identifier
                    )

                # Tenantcontact name
                other_q |= Q(
                    tenants__tenantcontact__contact__name__icontains=search_string
                )

                if " " in search_string:
                    tenant_name_parts = search_string.split(" ", 2)
                    other_q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=tenant_name_parts[
                            0
                        ]
                    ) & Q(
                        tenants__tenantcontact__contact__last_name__icontains=tenant_name_parts[
                            1
                        ]
                    )
                    other_q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=tenant_name_parts[
                            1
                        ]
                    ) & Q(
                        tenants__tenantcontact__contact__last_name__icontains=tenant_name_parts[
                            0
                        ]
                    )
                else:
                    other_q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=search_string
                    )
                    other_q |= Q(
                        tenants__tenantcontact__contact__last_name__icontains=search_string
                    )

                # Lessor
                other_q |= Q(lessor__name__icontains=search_string)
                other_q |= Q(lessor__first_name__icontains=search_string)
                other_q |= Q(lessor__last_name__icontains=search_string)

                # Date
                try:
                    search_date = parse(
                        search_string, parserinfo=parserinfo(dayfirst=True)
                    )
                    if search_date:
                        other_q |= Q(start_date=search_date.date())
                        other_q |= Q(end_date=search_date.date())
                except ValueError:
                    pass

            queryset = queryset.filter(identifier_q | other_q)

        # Advanced search
        search_form = LeaseSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get("tenant_name"):
                tenant_name = search_form.cleaned_data.get("tenant_name")

                # Tenantcontact name
                q = Q(tenants__tenantcontact__contact__name__icontains=tenant_name)

                if " " in tenant_name:
                    tenant_name_parts = tenant_name.split(" ", 2)
                    q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=tenant_name_parts[
                            0
                        ]
                    ) & Q(
                        tenants__tenantcontact__contact__last_name__icontains=tenant_name_parts[
                            1
                        ]
                    )
                    q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=tenant_name_parts[
                            1
                        ]
                    ) & Q(
                        tenants__tenantcontact__contact__last_name__icontains=tenant_name_parts[
                            0
                        ]
                    )
                else:
                    q |= Q(
                        tenants__tenantcontact__contact__first_name__icontains=tenant_name
                    )
                    q |= Q(
                        tenants__tenantcontact__contact__last_name__icontains=tenant_name
                    )

                if search_form.cleaned_data.get("tenantcontact_type"):
                    q &= Q(
                        tenants__tenantcontact__type__in=search_form.cleaned_data.get(
                            "tenantcontact_type"
                        )
                    )

                if search_form.cleaned_data.get("only_past_tenants"):
                    q &= Q(tenants__tenantcontact__end_date__lte=datetime.date.today())

                if search_form.cleaned_data.get("tenant_activity"):
                    if search_form.cleaned_data.get("tenant_activity") == "past":
                        q &= Q(
                            tenants__tenantcontact__end_date__lte=datetime.date.today()
                        )

                    if search_form.cleaned_data.get("tenant_activity") == "active":
                        # No need to filter by start date because future start dates are also considered active
                        q &= Q(tenants__tenantcontact__end_date=None) | Q(
                            tenants__tenantcontact__end_date__gte=datetime.date.today()
                        )

                queryset = queryset.filter(q)

            if search_form.cleaned_data.get("sequence"):
                queryset = queryset.filter(
                    identifier__sequence=search_form.cleaned_data.get("sequence")
                )

            if search_form.cleaned_data.get("lease_start_date_start"):
                queryset = queryset.filter(
                    start_date__gte=search_form.cleaned_data.get(
                        "lease_start_date_start"
                    )
                )

            if search_form.cleaned_data.get("lease_start_date_end"):
                queryset = queryset.filter(
                    start_date__lte=search_form.cleaned_data.get("lease_start_date_end")
                )

            if search_form.cleaned_data.get("lease_end_date_start"):
                queryset = queryset.filter(
                    end_date__gte=search_form.cleaned_data.get("lease_end_date_start")
                )

            if search_form.cleaned_data.get("lease_end_date_end"):
                queryset = queryset.filter(
                    end_date__lte=search_form.cleaned_data.get("lease_end_date_end")
                )

            # Filter by active / expired only when only one of the options is set
            if bool(search_form.cleaned_data.get("only_active_leases")) ^ bool(
                search_form.cleaned_data.get("only_expired_leases")
            ):
                if search_form.cleaned_data.get("only_active_leases"):
                    # No need to filter by start date because future start dates are also considered active
                    queryset = queryset.filter(
                        Q(end_date__isnull=True)
                        | Q(end_date__gte=datetime.date.today())
                    )

                if search_form.cleaned_data.get("only_expired_leases"):
                    queryset = queryset.filter(end_date__lte=datetime.date.today())

            if "has_geometry" in search_form.cleaned_data:
                if search_form.cleaned_data.get("has_geometry") is True:
                    queryset = queryset.exclude(lease_areas__geometry__isnull=True)

                if search_form.cleaned_data.get("has_geometry") is False:
                    queryset = queryset.exclude(lease_areas__geometry__isnull=False)

            if search_form.cleaned_data.get("property_identifier"):
                property_identifier = search_form.cleaned_data.get(
                    "property_identifier"
                )
                normalized_identifier = normalize_property_identifier(
                    property_identifier
                )

                queryset = queryset.filter(
                    Q(lease_areas__identifier__icontains=property_identifier)
                    | Q(lease_areas__identifier__icontains=normalized_identifier)
                )

            if search_form.cleaned_data.get("address"):
                queryset = queryset.filter(
                    lease_areas__addresses__address__icontains=search_form.cleaned_data.get(
                        "address"
                    )
                )

            if search_form.cleaned_data.get("lease_state"):
                queryset = queryset.filter(
                    state__in=search_form.cleaned_data.get("lease_state")
                )

            if search_form.cleaned_data.get("business_id"):
                queryset = queryset.filter(
                    tenants__tenantcontact__contact__business_id__icontains=search_form.cleaned_data.get(
                        "business_id"
                    )
                )

            if search_form.cleaned_data.get("national_identification_number"):
                nat_id = search_form.cleaned_data.get("national_identification_number")
                queryset = queryset.filter(
                    tenants__tenantcontact__contact__national_identification_number__icontains=nat_id
                )

            if search_form.cleaned_data.get("lessor"):
                queryset = queryset.filter(
                    lessor=search_form.cleaned_data.get("lessor")
                )

            if search_form.cleaned_data.get("contract_number"):
                queryset = queryset.filter(
                    contracts__contract_number__icontains=search_form.cleaned_data.get(
                        "contract_number"
                    )
                )

            if search_form.cleaned_data.get("decision_maker"):
                queryset = queryset.filter(
                    decisions__decision_maker=search_form.cleaned_data.get(
                        "decision_maker"
                    )
                )

            if search_form.cleaned_data.get("decision_date"):
                queryset = queryset.filter(
                    decisions__decision_date=search_form.cleaned_data.get(
                        "decision_date"
                    )
                )

            if search_form.cleaned_data.get("decision_section"):
                queryset = queryset.filter(
                    decisions__section=search_form.cleaned_data.get("decision_section")
                )

            if search_form.cleaned_data.get("reference_number"):
                reference_number = search_form.cleaned_data.get("reference_number")
                queryset = queryset.filter(
                    Q(reference_number__icontains=reference_number)
                    | Q(decisions__reference_number__icontains=reference_number)
                )

            if search_form.cleaned_data.get("invoice_number"):
                queryset = queryset.filter(
                    invoices__number__icontains=search_form.cleaned_data.get(
                        "invoice_number"
                    )
                )

        # filtering all leases with no decisions
        queryset = queryset.filter(decisions__isnull=False)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action in ("create", "metadata"):
            return LeaseCreateSerializer

        if self.action in ("update", "partial_update"):
            return LeaseUpdateSerializer

        if self.request.query_params.get("succinct"):
            return LeaseSuccinctSerializer

        if self.request.query_params.get("in_bbox") or self.request.query_params.get(
            "succinct_with_geometry"
        ):
            return LeaseSuccinctWithGeometrySerializer

        if self.action == "list":
            return LeaseListSerializer

        return LeaseRetrieveSerializer

    def perform_create(self, serializer):
        relate_to = None
        if "relate_to" in serializer.validated_data:
            relate_to = serializer.validated_data.pop("relate_to")

        relation_type = None
        if "relation_type" in serializer.validated_data:
            relation_type = serializer.validated_data.pop("relation_type")

        instance = serializer.save()

        if relate_to and relation_type:
            RelatedLease.objects.create(
                from_lease=relate_to, to_lease=instance, type=relation_type
            )

    def create(self, request, *args, **kwargs):
        if "preparer" not in request.data:
            request.data["preparer"] = request.user.id

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if (
            instance.preparer == request.user and instance.is_empty()
        ) or request.user.has_perm("leasing.delete_nonempty_lease"):
            self.perform_destroy(instance)

            return Response(status=status.HTTP_204_NO_CONTENT)

        raise PermissionDenied(_("No permission. Can only delete own empty leases."))
