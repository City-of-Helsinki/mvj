import argparse
import logging
import sys
from typing import Any, List, Optional

from django.core.management.base import BaseCommand

from ...models import JobRun, JobRunQuerySet


class Command(BaseCommand):
    help = "Batch Run Compact Log Entries"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("run_ids", type=int, nargs="+")

    def handle(
        self,
        run_ids: Optional[List[int]] = None,
        dry_run: bool = False,
        *args: Any,
        **kwargs: Any
    ) -> None:
        logging.basicConfig(
            level=logging.INFO, format="%(message)s", stream=sys.stdout,
        )

        for run_id in run_ids or []:
            self.process_job_run(run_id, dry_run=dry_run)

    def process_job_run(self, run_id: int, dry_run: bool = False) -> None:
        job_run_qs: JobRunQuerySet = JobRun.objects.filter(id=run_id)

        if not job_run_qs.exists():
            self.stderr.write("No job runs with id {}".format(run_id))
            raise SystemExit(1)

        job_run = job_run_qs.get()

        if dry_run:
            self.stdout.write(
                "Would compact {n} log entries of job run {i}: {r}".format(
                    n=job_run.log_entries.count(), i=job_run.id, r=job_run,
                )
            )
        else:
            compacted_entries = job_run_qs.compact_logs()
            self.stdout.write(
                "Compacted {n} entries of run id {i}".format(
                    n=compacted_entries, i=job_run.id
                )
            )
