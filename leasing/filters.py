from django.db.models import Exists, OuterRef, Q, QuerySet
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import OrderingFilter

from leasing.enums import TenantContactType
from leasing.models import (
    CollectionCourtDecision,
    CollectionLetter,
    CollectionNote,
    OldDwellingsInHousingCompaniesPriceIndex,
)
from leasing.models.invoice import InvoiceNote, InvoiceRow, InvoiceSet
from leasing.models.lease import LeaseType
from leasing.models.receivable_type import ReceivableType
from leasing.models.tenant import Tenant, TenantContact

from .models import (
    Comment,
    Contact,
    Decision,
    District,
    Index,
    IntendedUse,
    Invoice,
    Lease,
)


class CoalesceOrderingFilter(OrderingFilter):
    """Ordering filter that supports defining coalescent fields

    Coalescent fields are configured by adding a new attribute coalesce_ordering to the view.

    Example:

    ordering_fields = ('names',)
    coalesce_ordering = {"names": ("business_name", "last_name")}

    The coalesce field must be set in the views "ordering_fields" attribute. '__all__' will not work.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            if hasattr(view, "coalesce_ordering"):
                for ordering_term in ordering:
                    ordering_term = ordering_term.lstrip("-")

                    if ordering_term in view.coalesce_ordering:
                        kwargs = {
                            ordering_term: Coalesce(
                                *view.coalesce_ordering[ordering_term]
                            )
                        }
                        queryset = queryset.annotate(**kwargs)

            return queryset.order_by(*ordering)

        return queryset


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    """Number filter that accepts multiple values. Look up expr is 'in'"""


class CollectionCourtDecisionFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionCourtDecision
        fields = ["lease"]


class CollectionLetterFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionLetter
        fields = ["lease"]


class CollectionNoteFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionNote
        fields = ["lease", "user"]


class CommentFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = Comment
        fields = ["lease", "user", "topic"]


class ContactFilter(FilterSet):
    service_unit = NumberInFilter(field_name="service_unit_id")
    lease = filters.CharFilter(method="filter_lease")
    is_tenant = filters.BooleanFilter(method="filter_is_tenant")
    is_active = filters.BooleanFilter(method="filter_is_active")

    def filter_lease(self, queryset: QuerySet, parameter_name: str, value: str):
        if not value:
            return queryset

        return queryset.filter(
            # Use Exists subquery for performance when combining with other filters.
            Exists(
                Tenant.objects.filter(
                    contacts=OuterRef("pk"),
                    lease__identifier__identifier__icontains=value,
                    deleted__isnull=True,
                )
            )
        )

    def filter_is_tenant(self, queryset: QuerySet, parameter_name: str, value: bool):
        if not value:
            return queryset

        return queryset.filter(
            # Use Exists subquery for performance when combining with other filters.
            Exists(
                TenantContact.objects.filter(
                    contact_id=OuterRef("pk"),
                    type=TenantContactType.TENANT,
                    deleted__isnull=True,
                )
            )
        )

    def filter_is_active(self, queryset: QuerySet, parameter_name: str, value: bool):
        if not value:
            return queryset

        today = timezone.now().date()

        active_tenantcontact = TenantContact.objects.filter(
            contact_id=OuterRef("pk"),
            deleted__isnull=True,
        ).filter(
            Q(start_date__lte=today, end_date__isnull=True)
            | Q(start_date__lte=today, end_date__gte=today)
            | Q(start_date__isnull=True, end_date__isnull=True)
            | Q(start_date__isnull=True, end_date__gte=today)
        )

        active_lease = Tenant.objects.filter(
            contacts=OuterRef("pk"),
            deleted__isnull=True,
        ).filter(Q(lease__end_date__isnull=True) | Q(lease__end_date__gte=today))

        return queryset.filter(
            # Use Exists subquery for performance when combining with other filters.
            Exists(active_tenantcontact),
            Exists(active_lease),
        )

    class Meta:
        model = Contact
        fields = [
            "id",
            "type",
            "first_name",
            "last_name",
            "name",
            "business_id",
            "national_identification_number",
            "sap_customer_number",
            "partner_code",
            "is_lessor",
        ]


class DecisionFilter(FilterSet):
    lease = filters.NumberFilter()
    reference_number = filters.CharFilter(lookup_expr="contains")

    class Meta:
        model = Decision
        fields = [
            "lease",
            "reference_number",
            "decision_maker",
            "decision_date",
            "type",
        ]


class DistrictFilter(FilterSet):
    class Meta:
        model = District
        fields = ["municipality", "identifier"]


class IndexFilter(FilterSet):
    class Meta:
        model = Index
        fields = ["year", "month"]


class IntendedUseFilter(FilterSet):
    # For some reason the field `name` does not work for filtering
    search = filters.CharFilter(field_name="name_fi", lookup_expr="icontains")

    class Meta:
        model = IntendedUse
        fields = ["service_unit", "is_active"]


class LeaseTypeFilter(FilterSet):
    search = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = LeaseType
        fields = ["is_active"]


class InvoiceFilter(FilterSet):
    lease = filters.NumberFilter()
    going_to_sap = filters.BooleanFilter(
        method="filter_going_to_sap", label=_("Going to SAP")
    )
    service_unit = NumberInFilter(field_name="service_unit_id")

    class Meta:
        model = Invoice
        fields = ["lease", "state", "type"]

    def filter_going_to_sap(self, queryset: QuerySet, parameter_name: str, value: bool):
        if value:
            return queryset.filter(
                due_date__gte=timezone.now().date(), sent_to_sap_at__isnull=True
            )
        return queryset


class InvoiceNoteFilter(FilterSet):
    lease = filters.NumberFilter()
    service_unit = NumberInFilter(field_name="lease__service_unit")

    class Meta:
        model = InvoiceNote
        fields = ["lease"]


class InvoiceSetFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = InvoiceSet
        fields = ["lease"]


class InvoiceRowFilter(FilterSet):
    invoice = filters.NumberFilter()

    class Meta:
        model = InvoiceRow
        fields = ["invoice"]


class LeaseFilter(FilterSet):
    class Meta:
        model = Lease
        fields = ["type", "district"]


class OldDwellingsInHousingCompaniesPriceIndexFilter(FilterSet):
    class Meta:
        model = OldDwellingsInHousingCompaniesPriceIndex
        fields = "__all__"


class ReceivableTypeFilter(FilterSet):
    service_unit = NumberInFilter(field_name="service_unit_id")

    class Meta:
        model = ReceivableType
        fields = [
            "id",
            "name",
            "is_active",
            "service_unit__name",
        ]

class LeasesForContactOrderingFilter(OrderingFilter):
    """Standard `?ordering=` filter that maps serializer field names to the
    queryset fields/annotations that actually sort correctly.

    `identifier` is a relation, so it must sort by its string column;
    `contact_roles` is a list, so it sorts by the role count annotation.
    """

    ordering_aliases = {
        "lease_identifier": "identifier__identifier",
        "contact_roles": "contact_roles_count",
    }

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view) or []
        resolved = [
            (
                f"-{self.ordering_aliases[term[1:]]}"
                if term.startswith("-") and term[1:] in self.ordering_aliases
                else self.ordering_aliases.get(term, term)
            )
            for term in ordering
        ]
        # Append a unique tiebreaker so paginated ordering is deterministic;
        # boolean/count fields have many ties that otherwise shuffle per page.
        if not any(term.lstrip("-") == "pk" for term in resolved):
            resolved.append("pk")
        return resolved

