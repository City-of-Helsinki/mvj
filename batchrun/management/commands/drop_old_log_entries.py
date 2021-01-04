import argparse
from typing import Any

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand

from ...models import JobRun


class Command(BaseCommand):
    help = "JobRunLogEntry cleaner"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("retain_n_days", type=int, nargs="?", default=7)

    def handle(self, *args: Any, **options: Any) -> None:
        retain_n_days = options["retain_n_days"]

        latest_run = JobRun.objects.last()
        if not latest_run:
            self.stdout.write("No jobruns saved. Exiting...")
            return

        retain_from = latest_run.started_at - relativedelta(days=retain_n_days)
        retain_from = retain_from.replace(hour=0, minute=0, second=0, microsecond=0)
        runs_before_cutoff = JobRun.objects.filter(started_at__lt=retain_from)
        self.stdout.write(
            "Latest run started {}, sparing logs from jobs started after {}. JobRuns to delete {}, total {}".format(
                latest_run.started_at,
                retain_from,
                runs_before_cutoff.count(),
                JobRun.objects.count(),
            )
        )
        runs_before_cutoff.delete()

        self.stdout.write("Done!")
