from django.db.models import Q
from django_filters import filters
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import FilterSet

from forms.models import Answer
from leasing.models.land_area import LeaseAreaAddress
from plotsearch.models import PlotSearchTarget


class InitFilter(object):
    def init_filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs, True
        if self.distinct:
            return qs.distinct(), False
        return qs, False


class PlotSearchIdentificationFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.filter(
            targets__in=PlotSearchTarget.objects.filter(
                plan_unit__identifier__icontains=value
            )
        )
        return qs


class SimpleFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        address_qs = LeaseAreaAddress.objects.filter(address__icontains=value)
        pst_qs = PlotSearchTarget.objects.filter(
            Q(plan_unit__identifier__icontains=value)
            | Q(plan_unit__lease_area__addresses__in=address_qs)
        )
        qs = qs.filter(
            Q(targets__in=pst_qs)
            | Q(form__plotsearch__name__icontains=value)
            | Q(form__plotsearch__subtype__plot_search_type__name__icontains=value)
            | Q(form__plotsearch__subtype__name__icontains=value)
        )
        return qs


class AnswerFilterSet(FilterSet):
    plot_search = filters.NumberFilter(field_name="form__plotsearch__id")
    plot_search_type = filters.NumberFilter(
        field_name="form__plotsearch__subtype__plot_search_type__id"
    )
    plot_search_subtype = filters.NumberFilter(
        field_name="form__plotsearch__subtype__id"
    )
    begin_at = filters.DateFromToRangeFilter(field_name="form__plotsearch__begin_at")
    end_at = filters.DateFromToRangeFilter(field_name="form__plotsearch__end_at")
    state = filters.CharFilter(field_name="form__plotsearch__stage__name")
    identifier = PlotSearchIdentificationFilter()
    reserved = filters.BooleanFilter(field_name="statuses__reserved")
    q = SimpleFilter()

    class Meta:
        model = Answer
        fields = [
            "plot_search",
            "plot_search_type",
            "plot_search_subtype",
            "begin_at",
            "end_at",
            "state",
            "identifier",
            "reserved",
            "q",
        ]
