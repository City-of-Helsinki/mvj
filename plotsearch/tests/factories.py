import factory

from forms.tests.factories import AnswerFactory, EntrySectionFactory
from leasing.enums import PlotSearchTargetType
from leasing.tests.factories import LeaseFactory, PlanUnitFactory
from plotsearch.models import (
    AreaSearch,
    AreaSearchAttachment,
    AreaSearchIntendedUse,
    Favourite,
    InformationCheck,
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
    RelatedPlotApplication,
    TargetInfoLink,
    TargetStatus,
)


class AreaSearchIntendedUseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AreaSearchIntendedUse


class AreaSearchFactory(factory.django.DjangoModelFactory):
    intended_use = factory.SubFactory(AreaSearchIntendedUseFactory)

    class Meta:
        model = AreaSearch


class AreaSearchAttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AreaSearchAttachment


class FavouriteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Favourite


class PlotSearchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearch


class PlotSearchTargetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget


class PlotSearchTargetFactoryWithSubFactories(factory.django.DjangoModelFactory):
    plot_search = factory.SubFactory(PlotSearchFactory)
    plan_unit = factory.SubFactory(PlanUnitFactory)
    target_type = PlotSearchTargetType.SEARCHABLE

    class Meta:
        model = PlotSearchTarget


class PlotSearchTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchType


class PlotSearchSubtypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchSubtype


class PlotSearchStageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlotSearchStage


class InfoLinkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TargetInfoLink


class TargetStatusFactory(factory.django.DjangoModelFactory):
    plot_search_target = factory.SubFactory(PlotSearchTargetFactoryWithSubFactories)
    answer = factory.SubFactory(AnswerFactory)

    class Meta:
        model = TargetStatus


class InformationCheckFactory(factory.django.DjangoModelFactory):
    entry_section = factory.SubFactory(EntrySectionFactory)

    class Meta:
        model = InformationCheck


class RelatedPlotApplicationFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseFactory)
    content_object = factory.SubFactory(AreaSearchFactory, description_area="test")

    class Meta:
        model = RelatedPlotApplication
