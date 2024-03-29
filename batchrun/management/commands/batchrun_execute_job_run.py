import argparse
from typing import Any

from django.core.management.base import BaseCommand

from ...job_running import execute_job_run
from ...models import JobRun


class Command(BaseCommand):
    help = "Job Run Executor"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("job_run_id", type=int)

    def handle(self, *args: Any, **options: Any) -> None:
        job_run_id: int = options.get("job_run_id")  # type: ignore
        job_run = JobRun.objects.get(pk=job_run_id)
        execute_job_run(job_run)
