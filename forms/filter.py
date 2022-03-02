from django_filters import filters
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import FilterSet

from forms.models import Answer
from plotsearch.models import PlotSearch, PlotSearchTarget


class InitFilter(object):
    def init_filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs, True
        if self.distinct:
            return qs.distinct(), False


class PlotSearchFilter(InitFilter, filters.NumberFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(form__plotsearch__in=PlotSearch.objects.filter(pk=value))
        return qs


class PlotSearchTypeFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            form__plotsearch__in=PlotSearch.objects.filter(
                subtype__plot_search_type=value
            )
        )
        return qs


class PlotSearchSubTypeFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            form__plotsearch__in=PlotSearch.objects.filter(subtype=value)
        )
        return qs


class PlotSearchStartDateFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            form__plotsearch__in=PlotSearch.objects.filter(begin_at__lt=value)
        )
        return qs


class PlotSearchEndDateFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            form__plotsearch__in=PlotSearch.objects.filter(end_at__gte=value)
        )
        return qs


class PlotSearchStateFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            form__plotsearch__in=PlotSearch.objects.filter(stage=value)
        )
        return qs


class PlotSearchIdentificationFilter(InitFilter, filters.CharFilter):
    def filter(self, qs, value):
        qs, empty = self.init_filter(qs, value)
        if empty:
            return qs
        qs = qs.objects.filter(
            targets__in=PlotSearchTarget.objects.filter(plan_unit__identifier=value)
        )
        return qs


class AnswerFilterSet(FilterSet):
    plot_search = PlotSearchFilter()
    plot_search_type = PlotSearchTypeFilter()
    plot_search_subtype = PlotSearchSubTypeFilter()
    begin_at = PlotSearchStartDateFilter()
    end_at = PlotSearchEndDateFilter()
    state = PlotSearchStateFilter()
    identifier = PlotSearchIdentificationFilter()
    reserved = filters.BooleanFilter(field_name="statuses__reserved")

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
        ]