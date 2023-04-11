import django_filters
from django.db.models import Q
from django_filters.constants import EMPTY_VALUES

from plotsearch.models import AreaSearch, InformationCheck, TargetStatus


class TargetFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class InformationCheckListFilterSet(django_filters.FilterSet):
    answer = django_filters.NumberFilter(field_name="entry_section__answer")

    class Meta:
        model = InformationCheck
        fields = ("answer",)


class SimpleFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        qs = qs.filter(
            Q(address__icontains=value)
            | Q(intended_use__name__icontains=value)
            | Q(district__icontains=value)
            | Q(identifier__icontains=value)
            | Q(preparer__first_name__icontains=value)
            | Q(preparer__last_name__icontains=value)
            | Q(state=value)
            | Q(lessor=value)
        )
        return qs


class AreaSearchFilterSet(django_filters.FilterSet):
    area_search = django_filters.CharFilter(field_name="identifier")
    received_after = django_filters.DateFromToRangeFilter(
        field_name="received_date", lookup_expr="gte"
    )
    received_before = django_filters.DateFromToRangeFilter(
        field_name="received_date", lookup_expr="lt"
    )
    intended_use = django_filters.NumberFilter(field_name="intended_use__id")
    district = django_filters.CharFilter()
    lessor = django_filters.CharFilter(field_name="lessor")
    user = django_filters.CharFilter(field_name="user__username")
    begin_at = django_filters.DateFromToRangeFilter()
    end_at = django_filters.DateFromToRangeFilter()
    address = django_filters.CharFilter()
    preparer = django_filters.CharFilter(field_name="preparer__username")
    q = SimpleFilter()

    class Meta:
        model = AreaSearch
        fields = [
            "area_search",
            "received_after",
            "received_before",
            "intended_use",
            "district",
            "lessor",
            "user",
            "begin_at",
            "end_at",
            "address",
            "preparer",
            "q",
        ]


class TargetStatusExportFilterSet(django_filters.FilterSet):
    targets = TargetFilter(field_name="id")

    class Meta:
        model = TargetStatus
        fields = ("targets",)
