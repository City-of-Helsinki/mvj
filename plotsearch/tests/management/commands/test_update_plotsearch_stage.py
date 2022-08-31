from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from plotsearch.enums import SearchStage
from plotsearch.models import PlotSearch, PlotSearchStage


@pytest.mark.django_db
def test_stage_changes(django_db_setup, plot_search_test_data):
    now = timezone.now()
    plot_search_test_data.stage = PlotSearchStage.objects.get(pk=1)
    plot_search_test_data.begin_at = now - timedelta(minutes=10)
    plot_search_test_data.end_at = now + timedelta(days=1)
    plot_search_test_data.save()

    call_command("update_plotsearch_stage")

    assert PlotSearch.objects.get(
        name=plot_search_test_data.name
    ).stage == PlotSearchStage.objects.get(stage=SearchStage.IN_ACTION)

    plot_search_test_data = PlotSearch.objects.get(name=plot_search_test_data.name)
    plot_search_test_data.end_at = now - timedelta(days=1)
    plot_search_test_data.save()

    call_command("update_plotsearch_stage")

    assert PlotSearch.objects.get(
        name=plot_search_test_data.name
    ).stage == PlotSearchStage.objects.get(stage=SearchStage.PROCESSING)
