from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from field_permissions.viewsets import FieldPermissionsViewsetMixin
from leasing.forms import BasisOfRentSearchForm
from leasing.models import BasisOfRent
from leasing.serializers.basis_of_rent import BasisOfRentCreateUpdateSerializer, BasisOfRentSerializer

from .utils import AtomicTransactionModelViewSet, AuditLogMixin


class BasisOfRentViewSet(AuditLogMixin, FieldPermissionsViewsetMixin, AtomicTransactionModelViewSet):
    queryset = BasisOfRent.objects.all()
    serializer_class = BasisOfRentSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('detailed_plan_identifier', 'note', 'property_identifiers__identifier')
    ordering_fields = ('start_date', 'end_date', 'detailed_plan_identifier', 'plot_type__name')
    ordering = ('-start_date', '-end_date')

    def get_queryset(self):
        queryset = BasisOfRent.objects.select_related('plot_type', 'management', 'financing', 'index').prefetch_related(
            'rent_rates', 'property_identifiers', 'decisions', 'decisions__decision_maker')

        if self.action != 'list':
            return queryset

        search_form = BasisOfRentSearchForm(self.request.query_params)

        if search_form.is_valid():
            if search_form.cleaned_data.get('search'):
                search_text = search_form.cleaned_data.get('search')
                queryset = queryset.filter(
                    Q(detailed_plan_identifier__icontains=search_text) |
                    Q(note__icontains=search_text) |
                    Q(property_identifiers__identifier__icontains=search_text)
                )

            if search_form.cleaned_data.get('decision_maker'):
                queryset = queryset.filter(decisions__decision_maker=search_form.cleaned_data.get('decision_maker'))

            if search_form.cleaned_data.get('decision_date'):
                queryset = queryset.filter(decisions__decision_date=search_form.cleaned_data.get('decision_date'))

            if search_form.cleaned_data.get('decision_section'):
                queryset = queryset.filter(decisions__section=search_form.cleaned_data.get('decision_section'))

            if search_form.cleaned_data.get('reference_number'):
                queryset = queryset.filter(decisions__reference_number__icontains=search_form.cleaned_data.get(
                    'reference_number'))

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return BasisOfRentCreateUpdateSerializer

        return BasisOfRentSerializer
