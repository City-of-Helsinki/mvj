import argparse
import logging
import sys
from typing import Any

from django.core.management.base import BaseCommand

from ...history_cleaning import perform_job_run_log_rotate_and_clean_up


class Command(BaseCommand):
    help = "Batch Run Log Rotate"

    @classmethod
    def add_arguments(cls, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, dry_run: bool = False, *args: Any, **kwargs: Any) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=sys.stdout,
        )
        perform_job_run_log_rotate_and_clean_up(dry_run=dry_run)
