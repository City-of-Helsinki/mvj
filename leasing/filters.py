from django.db.models.functions import Coalesce
from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import OrderingFilter

from leasing.models import CollectionCourtDecision, CollectionLetter, CollectionNote
from leasing.models.invoice import InvoiceRow, InvoiceSet

from .models import Comment, Contact, Decision, District, Index, Invoice, Lease


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
            if hasattr(view, 'coalesce_ordering'):
                for ordering_term in ordering:
                    ordering_term = ordering_term.lstrip('-')

                    if ordering_term in view.coalesce_ordering:
                        kwargs = {
                            ordering_term: Coalesce(*view.coalesce_ordering[ordering_term])
                        }
                        queryset = queryset.annotate(**kwargs)

            return queryset.order_by(*ordering)

        return queryset


class CollectionCourtDecisionFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionCourtDecision
        fields = ['lease']


class CollectionLetterFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionLetter
        fields = ['lease']


class CollectionNoteFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = CollectionNote
        fields = ['lease', 'user']


class CommentFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = Comment
        fields = ['lease', 'user', 'topic']


class ContactFilter(FilterSet):
    class Meta:
        model = Contact
        fields = ['type', 'first_name', 'last_name', 'name', 'business_id', 'national_identification_number',
                  'customer_number', 'sap_customer_number', 'partner_code', 'is_lessor']


class DecisionFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = Decision
        fields = ['lease', 'reference_number', 'decision_maker', 'decision_date', 'type']


class DistrictFilter(FilterSet):
    class Meta:
        model = District
        fields = ['municipality', 'identifier']


class IndexFilter(FilterSet):
    class Meta:
        model = Index
        fields = ['year', 'month']


class InvoiceFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = Invoice
        fields = ['lease', 'state', 'type']


class InvoiceSetFilter(FilterSet):
    lease = filters.NumberFilter()

    class Meta:
        model = InvoiceSet
        fields = ['lease']


class InvoiceRowFilter(FilterSet):
    invoice = filters.NumberFilter()

    class Meta:
        model = InvoiceRow
        fields = ['invoice']


class LeaseFilter(FilterSet):
    class Meta:
        model = Lease
        fields = ['type', 'municipality', 'district']
