import django_filters

from plotsearch.models import InformationCheck


class InformationCheckListFilterSet(django_filters.FilterSet):
    answer = django_filters.NumberFilter(field_name="entry_section__answer")

    class Meta:
        model = InformationCheck
        fields = ("answer",)
