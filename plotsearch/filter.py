import operator
from functools import reduce

import django_filters
from django.db.models import Q
from django_filters.constants import EMPTY_VALUES

from forms.models import Answer, Entry, EntrySection
from plotsearch.enums import SearchStage
from plotsearch.models import AreaSearch, InformationCheck, PlotSearch, TargetStatus
from plotsearch.models.plot_search import PlotSearchStage


class TargetFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class AreaSearchIDFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class InformationCheckListFilterSet(django_filters.FilterSet):
    answer = django_filters.NumberFilter(field_name="entry_section__answer")

    class Meta:
        model = InformationCheck
        fields = ("answer",)


class ApplicantMixin:
    @staticmethod
    def filter_applicants(qs, value):
        company_entrysection_qs = EntrySection.objects.filter(
            entries__field__identifier="hakija",
            entries__field__section__identifier="hakijan-tiedot",
            entries__value="1",
        )
        person_entrysection_qs = EntrySection.objects.filter(
            entries__field__identifier="hakija",
            entries__field__section__identifier="hakijan-tiedot",
            entries__value="2",
        )
        company_entry_qs = Entry.objects.filter(
            field__identifier="yrityksen-nimi",
            field__section__identifier="yrityksen-tiedot",
            entry_section__in=company_entrysection_qs,
            value__icontains=value,
        )
        names = value.split(" ")
        front_name_entry_qs = Entry.objects.filter(
            field__identifier="etunimi",
            field__section__identifier="henkilon-tiedot",
            entry_section__in=person_entrysection_qs,
        ).filter(reduce(operator.or_, (Q(value__icontains=name) for name in names)))
        last_name_entry_qs = Entry.objects.filter(
            field__identifier="Sukunimi",
            field__section__identifier="henkilon-tiedot",
            entry_section__in=person_entrysection_qs,
        ).filter(reduce(operator.or_, (Q(value__icontains=name) for name in names)))

        answer_qs = Answer.objects.filter(
            Q(entry_sections__entries__in=company_entry_qs)
            | Q(entry_sections__entries__in=front_name_entry_qs)
            | Q(entry_sections__entries__in=last_name_entry_qs)
        )
        return answer_qs


class AreaSearchSimpleFilter(ApplicantMixin, django_filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        answer_qs = self.filter_applicants(qs, value)
        qs = qs.filter(
            Q(address__icontains=value)
            | Q(intended_use__name__icontains=value)
            | Q(district__icontains=value)
            | Q(identifier__icontains=value)
            | Q(preparer__first_name__icontains=value)
            | Q(preparer__last_name__icontains=value)
            | Q(answer__in=answer_qs)
        )
        return qs


class AreaSearchDistrictFilter(django_filters.FilterSet):
    district = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = AreaSearch
        fields = [
            "district",
        ]


class PlotSearchSimpleFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        qs = qs.filter(
            Q(name__icontains=value)
            | Q(subtype__name__icontains=value)
            | Q(subtype__plot_search_type__name__icontains=value)
            | Q(stage__name__icontains=value)
        )
        return qs


class ApplicantFilter(ApplicantMixin, django_filters.CharFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        answer_qs = self.filter_applicants(qs, value)
        return qs.filter(answer__in=answer_qs)


class ManyCharFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


class AreaSearchFilterSet(django_filters.FilterSet):
    identifier = django_filters.CharFilter(lookup_expr="icontains")
    ids = AreaSearchIDFilter(field_name="id")
    received_date = django_filters.DateFromToRangeFilter()
    intended_use = django_filters.NumberFilter(field_name="intended_use__id")
    district = django_filters.CharFilter(lookup_expr="icontains")
    lessor = django_filters.CharFilter(field_name="lessor")
    state = ManyCharFilter(field_name="state")
    user = django_filters.CharFilter(field_name="user__username")
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()
    address = django_filters.CharFilter(lookup_expr="icontains")
    preparer = django_filters.CharFilter(field_name="preparer__id")
    applicant = ApplicantFilter()
    service_unit = django_filters.NumberFilter(field_name="service_unit__id")
    q = AreaSearchSimpleFilter()

    class Meta:
        model = AreaSearch
        fields = [
            "identifier",
            "ids",
            "received_date",
            "intended_use",
            "district",
            "lessor",
            "user",
            "start_date",
            "end_date",
            "address",
            "preparer",
            "applicant",
            "state",
            "q",
        ]


class TargetStatusExportFilterSet(django_filters.FilterSet):
    targets = TargetFilter(field_name="id")

    class Meta:
        model = TargetStatus
        fields = ("targets",)


class PlotSearchFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    type = django_filters.NumberFilter(field_name="subtype__plot_search_type")
    begin_at = django_filters.DateFromToRangeFilter()
    end_at = django_filters.DateFromToRangeFilter()
    q = PlotSearchSimpleFilter()

    class Meta:
        model = PlotSearch
        fields = ("q", "name", "search_class", "stage", "type", "subtype")


class PlotSearchPublicFilterSet(django_filters.FilterSet):
    type = django_filters.NumberFilter(field_name="subtype__plot_search_type")
    # For public API, only show plot searches that are 'in_action'
    stage = django_filters.ModelChoiceFilter(
        queryset=PlotSearchStage.objects.filter(stage=SearchStage.IN_ACTION)
    )

    class Meta:
        model = PlotSearch
        fields = ("search_class", "stage", "type", "subtype")
