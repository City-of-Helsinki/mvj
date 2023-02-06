import django_filters

from plotsearch.models import InformationCheck, TargetStatus


class TargetFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class InformationCheckListFilterSet(django_filters.FilterSet):
    answer = django_filters.NumberFilter(field_name="entry_section__answer")

    class Meta:
        model = InformationCheck
        fields = ("answer",)


class TargetStatusExportFilterSet(django_filters.FilterSet):
    targets = TargetFilter(field_name="id")

    class Meta:
        model = TargetStatus
        fields = ("targets",)
