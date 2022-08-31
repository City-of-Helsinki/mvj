from django.core.management import BaseCommand
from django.utils import timezone

from plotsearch.enums import SearchStage
from plotsearch.models import PlotSearch, PlotSearchStage


class Command(BaseCommand):
    help = "Update plotsearch stage"

    def handle(self, *args, **options):
        now = timezone.now()

        in_preparation_plot_search_qs = PlotSearch.objects.filter(
            stage__stage=SearchStage.IN_PREPARATION
        )

        if in_preparation_plot_search_qs.exists():
            going_to_in_action_plot_search_qs = in_preparation_plot_search_qs.filter(
                begin_at__lte=now
            )
            in_action_stage = PlotSearchStage.objects.get(stage=SearchStage.IN_ACTION)
            going_to_in_action_plot_search_qs.update(stage=in_action_stage)

        in_action_plot_search_qs = PlotSearch.objects.filter(
            stage__stage=SearchStage.IN_ACTION
        )
        if in_action_plot_search_qs.exists():
            going_to_processing_plot_search_qs = in_action_plot_search_qs.filter(
                end_at__lte=now
            )
            processed_stage = PlotSearchStage.objects.get(stage=SearchStage.PROCESSING)
            going_to_processing_plot_search_qs.update(stage=processed_stage)
