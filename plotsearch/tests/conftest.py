import factory
import pytest
from django.utils import timezone
from pytest_factoryboy import register

from plotsearch.models import (
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
)


@pytest.fixture
def plot_search_test_data(
    plot_search_factory,
    plot_search_type_factory,
    plot_search_subtype_factory,
    plot_search_stage_factory,
    user_factory,
):
    plot_search_type = plot_search_type_factory(name="Test type")
    plot_search_subtype = plot_search_subtype_factory(
        name="Test subtype", plot_search_type=plot_search_type
    )
    plot_search_stage = plot_search_stage_factory(name="Test stage")
    preparer = user_factory(username="test_preparer")

    begin_at = timezone.now().replace(microsecond=0)
    end_at = (timezone.now() + timezone.timedelta(days=7)).replace(microsecond=0)

    plot_search = plot_search_factory(
        name="PS1",
        subtype=plot_search_subtype,
        stage=plot_search_stage,
        preparer=preparer,
        begin_at=begin_at,
        end_at=end_at,
    )

    return plot_search


@register
class PlotSearchFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearch


@register
class PlotSearchTargetFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget


@register
class PlotSearchTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchType


@register
class PlotSearchSubtypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchSubtype


@register
class PlotSearchStageFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchStage
