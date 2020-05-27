from django.db.models import Q
from rest_framework.filters import OrderingFilter

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.forms import InfillDevelopmentCompensationSearchForm
from leasing.models import (
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationAttachment,
)
from leasing.serializers.infill_development_compensation import (
    InfillDevelopmentCompensationAttachmentCreateUpdateSerializer,
    InfillDevelopmentCompensationAttachmentSerializer,
    InfillDevelopmentCompensationCreateUpdateSerializer,
    InfillDevelopmentCompensationSerializer,
)

from .utils import (
    AtomicTransactionModelViewSet,
    AuditLogMixin,
    FileMixin,
    MultiPartJsonParser,
)


class InfillDevelopmentCompensationViewSet(
    AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet
):
    queryset = InfillDevelopmentCompensation.objects.all()
    serializer_class = InfillDevelopmentCompensationSerializer
    filter_backends = (OrderingFilter,)
    ordering_fields = (
        "name",
        "detailed_plan_identifier",
        "state",
        "lease_contract_change_date",
        "reference_number",
    )
    ordering = ("name",)

    def get_queryset(self):
        queryset = InfillDevelopmentCompensation.objects.select_related(
            "user"
        ).prefetch_related(
            "infill_development_compensation_leases",
            "infill_development_compensation_leases__lease",
            "infill_development_compensation_leases__lease__identifier",
            "infill_development_compensation_leases__lease__type",
            "infill_development_compensation_leases__lease__municipality",
            "infill_development_compensation_leases__lease__district",
            "infill_development_compensation_leases__lease__identifier__type",
            "infill_development_compensation_leases__lease__identifier__municipality",
            "infill_development_compensation_leases__lease__identifier__district",
        )

        if self.action != "list":
            return queryset

        search_form = InfillDevelopmentCompensationSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get("search"):
                search_text = search_form.cleaned_data.get("search")
                queryset = queryset.filter(
                    Q(name__icontains=search_text)
                    | Q(detailed_plan_identifier__icontains=search_text)
                    | Q(note__icontains=search_text)
                )

            if search_form.cleaned_data.get("state"):
                queryset = queryset.filter(
                    state__in=search_form.cleaned_data.get("state")
                )

            if search_form.cleaned_data.get("decision_maker"):
                queryset = queryset.filter(
                    infill_development_compensation_leases__decisions__decision_maker=search_form.cleaned_data.get(
                        "decision_maker"
                    )
                )

            if search_form.cleaned_data.get("decision_date"):
                queryset = queryset.filter(
                    infill_development_compensation_leases__decisions__decision_date=search_form.cleaned_data.get(
                        "decision_date"
                    )
                )

            if search_form.cleaned_data.get("decision_section"):
                queryset = queryset.filter(
                    infill_development_compensation_leases__decisions__section=search_form.cleaned_data.get(
                        "decision_section"
                    )
                )

            if search_form.cleaned_data.get("reference_number"):
                reference_number = search_form.cleaned_data.get("reference_number")
                queryset = queryset.filter(
                    Q(reference_number__icontains=reference_number)
                    | Q(
                        infill_development_compensation_leases__decisions__reference_number__icontains=reference_number
                    )
                )

        return queryset

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return InfillDevelopmentCompensationCreateUpdateSerializer

        return InfillDevelopmentCompensationSerializer


class InfillDevelopmentCompensationAttachmentViewSet(
    FileMixin,
    AuditLogMixin,
    FieldPermissionsViewsetMixin,
    AtomicTransactionModelViewSet,
):
    queryset = InfillDevelopmentCompensationAttachment.objects.all()
    serializer_class = InfillDevelopmentCompensationAttachmentSerializer
    parser_classes = (MultiPartJsonParser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update", "metadata"):
            return InfillDevelopmentCompensationAttachmentCreateUpdateSerializer

        return InfillDevelopmentCompensationAttachmentSerializer
