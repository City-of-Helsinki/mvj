import enum
import logging
from typing import Dict, Iterable, Optional, Set

from django.db import models
from django.utils import timezone

from .models import JobRun, JobRunQuerySet

LOG = logging.getLogger(__name__)


class CleanAction(enum.Enum):
    DELETE_RUN = enum.auto()
    DELETE_LOGS = enum.auto()
    COMPACT_LOGS = enum.auto()


ActionsMap = Dict[CleanAction, Set[int]]


def perform_job_run_log_rotate_and_clean_up(dry_run: bool = False) -> None:
    """
    Perform log rotating and cleaning of information of job runs.

    Time schedule for the clean actions is determined by the
    JobHistoryRetentionPolicy objects which are assigned to the
    history_retention_policy field of the Job objects related to the
    JobRun objects.
    """
    cleaner = JobRunHistoryCleaner(dry_run=dry_run)
    try:
        actions = cleaner.clean()

        performed = "performed" if not dry_run else "to be performed"
        for action in sorted(actions, key=(lambda x: x.name)):
            ids = actions[action]
            if ids:
                LOG.info(
                    f"Clean-up statistics: Total %s actions {performed}: %s",
                    action.name,
                    len(ids),
                )
    finally:
        LOG.info(
            "Deleted %s job run objects, %s compact logs and %s log entries",
            cleaner.runs_deleted,
            cleaner.compact_logs_deleted,
            cleaner.log_entries_deleted,
        )


class JobRunHistoryCleaner:
    def __init__(self, dry_run: bool = False) -> None:
        self.clean_time = timezone.now()
        self.dry_run = dry_run
        self.runs_deleted = 0
        self.compact_logs_deleted = 0
        self.log_entries_deleted = 0

    def clean(self, actions: Optional[ActionsMap] = None) -> ActionsMap:
        if actions is None:
            actions = self.collect_todo_actions()
        self._execute_delete_runs(actions.get(CleanAction.DELETE_RUN, []))
        self._execute_delete_logs(actions.get(CleanAction.DELETE_LOGS, []))
        self._execute_compact_logs(actions.get(CleanAction.COMPACT_LOGS, []))
        return actions

    def collect_todo_actions(self) -> ActionsMap:
        to_delete = self._filter_runs_by_delay_field("delete_run_delay")

        del_logs_pre = self._filter_runs_by_delay_field("delete_logs_delay")
        to_delete_logs = del_logs_pre.has_logs().exclude(pk__in=to_delete)

        to_compact_pre = self._filter_runs_by_delay_field("compact_logs_delay")
        to_compact = (
            to_compact_pre.exclude(pk__in=to_delete)
            .exclude(pk__in=to_delete_logs)
            .has_log_entries()
        )

        action_qs_pairs = [
            (CleanAction.DELETE_RUN, to_delete),
            (CleanAction.DELETE_LOGS, to_delete_logs),
            (CleanAction.COMPACT_LOGS, to_compact),
        ]

        for (action, qs) in action_qs_pairs:
            for run in qs:
                LOG.info(
                    "Planning clean action %s for run %s (%s + %s -> %s) | %s",
                    f"{action.name:12}",
                    f"{run.pk:6}",
                    run.started_at,
                    f"{run.delay!s:>20}",  # type: ignore
                    run.delay_elapsed_at,  # type: ignore
                    run,
                )

        return {
            action: set(qs.values_list("pk", flat=True))
            for (action, qs) in action_qs_pairs
        }

    def _filter_runs_by_delay_field(self, field: str) -> JobRunQuerySet:
        result = (
            JobRun.objects.all()
            .annotate(delay=models.F(f"job__history_retention_policy__{field}"))
            .annotate(
                delay_elapsed_at=models.ExpressionWrapper(
                    models.F("started_at") + models.F("delay"),
                    output_field=models.DateTimeField(),
                )
            )
            .filter(delay_elapsed_at__lte=self.clean_time)
        )
        return result  # type: ignore

    def _execute_delete_runs(self, run_ids: Iterable[int]) -> None:
        for batch in self._jobrun_batches(run_ids):
            deleting = "Deleting" if not self.dry_run else "Would delete"
            batch_run_ids = ", ".join(str(x.id) for x in batch)
            LOG.info(f"{deleting} information of job runs: %s", batch_run_ids)
            if not self.dry_run:
                delete_counts = batch.delete_with_logs()
                (runs_deleted, logs_deleted, entries_deleted) = delete_counts
                self.runs_deleted += runs_deleted
                self.compact_logs_deleted += logs_deleted
                self.log_entries_deleted += entries_deleted

    def _jobrun_batches(self, ids: Iterable[int]) -> Iterable[JobRunQuerySet]:
        ids_left = sorted(ids)
        while ids_left:
            batch = JobRun.objects.filter(pk__in=ids_left[:10])
            ids_left = ids_left[10:]
            yield batch  # type: ignore

    def _execute_delete_logs(self, run_ids: Iterable[int]) -> None:
        runs: JobRunQuerySet = JobRun.objects.filter(pk__in=run_ids)  # type: ignore
        if not self.dry_run:
            (deleted_logs, deleted_entries) = runs.delete_logs()
            self.compact_logs_deleted += deleted_logs
            self.log_entries_deleted += deleted_entries

    def _execute_compact_logs(self, run_ids: Iterable[int]) -> None:
        runs: JobRunQuerySet = JobRun.objects.filter(pk__in=run_ids)  # type: ignore
        if not self.dry_run:
            entries_deleted = runs.compact_logs()
            self.log_entries_deleted += entries_deleted
