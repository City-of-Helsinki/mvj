import logging
import shlex
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

import pytz
from django.core.exceptions import ValidationError
from django.db import connections, models, transaction
from django.db.models.fields.json import JSONField  # type: ignore
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ugettext
from enumfields import EnumField, EnumIntegerField
from safedelete.models import SafeDeleteModel

from ._times import utc_now
from .compactor import CompactLog
from .constants import GRACE_PERIOD_LENGTH, LINE_END_CHARACTERS
from .enums import CommandType, LogEntryKind
from .fields import IntegerSetSpecifierField, TextJSONField
from .model_mixins import CleansOnSave, TimeStampedModel, TimeStampedSafeDeleteModel
from .scheduling import RecurrenceRule
from .utils import get_django_manage_py

LOG = logging.getLogger(__name__)


if TYPE_CHECKING:
    QuerySet = models.QuerySet
else:
    QuerySet = defaultdict(lambda: models.QuerySet)


class Command(SafeDeleteModel):
    type = EnumField(CommandType, max_length=30)

    name = models.CharField(
        max_length=1000,
        verbose_name=_("name"),
        help_text=_(
            "Name of the command to run e.g. "
            "name of a program in PATH or a full path to an executable, or "
            "name of a management command."
        ),
    )

    # type definition for each parameter, e.g.:
    #   {
    #     "rent_id": {
    #       "type": "int",
    #       "required": false,
    #       "description": {
    #         "fi": "Vuokrauksen tunnus",
    #         "sv": ...
    #       }
    #     },
    #     "time_range_start": {"type": "datetime", "required": true},
    #     "time_range_end": ...
    #   }
    parameters = JSONField(default=dict, blank=True, verbose_name=_("parameters"))
    parameter_format_string = models.CharField(
        max_length=1000,
        default="",
        blank=True,
        verbose_name=_("parameter format string"),
        help_text=_(
            "String that defines how the parameters are formatted "
            "when calling the command. E.g. if this is "
            '"--rent-id {rent_id}" and value 123 is passed as '
            "an argument to the rent_id parameter, then the command "
            'will be called as "COMMAND --rent-id 123".'
        ),
    )

    class Meta:
        verbose_name = _("command")
        verbose_name_plural = _("commands")

    def __str__(self) -> str:
        return "{type}: {name}{space}{params}".format(
            type=self.type,
            name=self.name,
            space=" " if self.parameter_format_string else "",
            params=self.parameter_format_string,
        )

    def get_command_line(self, arguments: Dict[str, Any]) -> List[str]:
        if self.type == CommandType.EXECUTABLE:
            base_command = [self.name]
        elif self.type == CommandType.DJANGO_MANAGE:
            base_command = [sys.executable, get_django_manage_py(), self.name]
        else:
            raise ValueError("Unknown command type: {}".format(self.type))
        formatted_args = [
            param_template.format(**arguments)
            for param_template in shlex.split(self.parameter_format_string)
        ]
        return base_command + formatted_args


class JobHistoryRetentionPolicy(models.Model):
    identifier = models.CharField(
        max_length=30, unique=True, verbose_name=_("identifier")
    )
    compact_logs_delay = models.DurationField(
        default=timedelta(days=14),  # 2 weeks
        verbose_name=_("log compacting delay"),
        help_text=_(
            "Days to wait before compacting log entries. "
            "Calculated from the start time of the job. "
            "Compacting log entries means that the individual "
            "log entries are concatenated to a single string and the "
            "original entries are deleted. This allows PostgreSQL "
            'to compress the log contents (check "TOAST" from '
            "PostgreSQL documentation). The metadata information about "
            "the log entry kinds (stdout/stderr) and timestamps are "
            "stored separately so that the original contents of the log "
            "entries are still recoverable."
        ),
    )
    delete_logs_delay = models.DurationField(
        default=timedelta(days=1461),  # 4 years
        verbose_name=_("log deleting delay"),
        help_text=_(
            "Days to wait before deleting logs. "
            "Calculated from the start time of the job."
        ),
    )
    delete_run_delay = models.DurationField(
        default=timedelta(days=3652),  # 10 years
        verbose_name=_("run inforomation deleting delay"),
        help_text=_(
            "Days to wait before deleting all inforomation about the run. "
            "Calculated from the start time of the job."
        ),
    )

    class Meta:
        verbose_name = _("job history retention policy")
        verbose_name_plural = _("job history retention policies")

    def __str__(self) -> str:
        return self.identifier

    @classmethod
    def get_default(cls) -> "JobHistoryRetentionPolicy":
        return cls.objects.get_or_create(identifier="default")[0]


def _get_default_job_history_retention_policy_pk() -> int:
    return JobHistoryRetentionPolicy.get_default().pk  # type: ignore


class Job(TimeStampedSafeDeleteModel):
    """
    Unit of work that can be ran by the system.

    Job is basically a Command with predefined arguments to be passed as
    the parameters for the command.  E.g. command can be Django's
    "migrate" management command and a job could then be "Migrate app1"
    which passes in the "app1" argument as "app_label" parameter.
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_("name"),
        help_text=_("Descriptive name for the job"),
    )
    comment = models.CharField(max_length=500, blank=True, verbose_name=_("comment"))

    command = models.ForeignKey(
        Command, on_delete=models.PROTECT, verbose_name=_("command")
    )
    arguments = JSONField(
        default=dict,
        blank=True,
        verbose_name=_("arguments"),
        help_text=_(
            "Argument for the command as a JSON object. These will be "
            "formatted with the parameter format string of the command. "
            "E.g. to pass value 123 as an argument to the rent_id "
            'parameter, set this to {"rent_id": 123}.'
        ),
    )
    history_retention_policy = models.ForeignKey(
        JobHistoryRetentionPolicy,
        default=_get_default_job_history_retention_policy_pk,
        on_delete=models.PROTECT,
        verbose_name=_("history retention policy"),
        help_text=_(
            "Defines how long logs and information about "
            "completed runs is preserved."
        ),
    )

    class Meta:
        verbose_name = _("job")
        verbose_name_plural = _("jobs")

    def __str__(self) -> str:
        return self.name

    def get_command_line(self) -> List[str]:
        return self.command.get_command_line(self.arguments)


class Timezone(CleansOnSave, models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_("name"),
        help_text=_(
            'Name of the timezone, e.g. "Europe/Helsinki" or "UTC". See '
            "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones "
            "for a list of possible values."
        ),
    )

    class Meta:
        verbose_name = _("timezone")
        verbose_name_plural = _("timezones")

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        try:
            pytz.timezone(self.name or "")
        except KeyError:
            raise ValidationError({"name": _("Invalid timezone name")})
        super().clean()


class ScheduledJob(TimeStampedModel):
    """
    Scheduling for a job to be ran at certain moment(s).

    The scheduling can define the job to be run just once or as a series
    of recurring events.
    """

    job = models.ForeignKey(Job, on_delete=models.PROTECT, verbose_name=_("job"))

    comment = models.CharField(max_length=500, blank=True, verbose_name=_("comment"))

    enabled = models.BooleanField(
        default=True, db_index=True, verbose_name=_("enabled")
    )

    timezone = models.ForeignKey(
        Timezone, on_delete=models.PROTECT, verbose_name=_("timezone")
    )
    years = IntegerSetSpecifierField(value_range=(1970, 2200), verbose_name=_("years"))
    months = IntegerSetSpecifierField(value_range=(1, 12), verbose_name=_("months"))
    days_of_month = IntegerSetSpecifierField(
        value_range=(1, 31), verbose_name=_("days of month")
    )
    weekdays = IntegerSetSpecifierField(
        value_range=(0, 6),
        verbose_name=_("weekdays"),
        help_text=_(
            "Limit execution to specified weekdays. Use integer values "
            "to represent the weekdays with the following mapping: "
            "0=Sunday, 1=Monday, 2=Tuesday, ..., 6=Saturday."
        ),
    )
    hours = IntegerSetSpecifierField(value_range=(0, 23), verbose_name=_("hours"))
    minutes = IntegerSetSpecifierField(value_range=(0, 59), verbose_name=_("minutes"))

    class Meta:
        verbose_name = _("scheduled job")
        verbose_name_plural = _("scheduled jobs")

    def __str__(self) -> str:
        time_fields = [
            "years",
            "months",
            "days_of_month",
            "weekdays",
            "hours",
            "minutes",
        ]
        schedule_items = []
        for field in time_fields:
            value = getattr(self, field)
            key = field[0] if field not in ["hours", "minutes"] else field[0].upper()
            schedule_items.append(f"{key}={value}")
        return ugettext('Scheduled job "{job}" @ {schedule}').format(
            job=self.job, schedule=" ".join(schedule_items)
        )

    @property
    def recurrence_rule(self) -> RecurrenceRule:
        return RecurrenceRule.create(
            timezone=self.timezone.name,
            years=self.years,
            months=self.months,
            days_of_month=self.days_of_month,
            weekdays=self.weekdays,
            hours=self.hours,
            minutes=self.minutes,
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        self.update_run_queue()

    def update_run_queue(self, max_items_to_create: int = 10) -> None:
        items: models.Manager = self.run_queue_items  # type: ignore
        start_from = utc_now() - GRACE_PERIOD_LENGTH

        fresh_ids = []

        if self.enabled:
            events = self.recurrence_rule.get_next_events(start_from)
            for (number, time) in enumerate(events):
                if number >= max_items_to_create:
                    break
                item = items.get_or_create(run_at=time, scheduled_job=self)[0]
                fresh_ids.append(item.pk)

        # Delete old items
        items.exclude(pk__in=fresh_ids).delete()


class JobRunQuerySet(QuerySet["JobRun"]):
    def has_logs(self) -> "JobRunQuerySet":
        has_compacted_log = models.Q(pk__in=self.has_compacted_log())
        has_log_entries = models.Q(pk__in=self.has_log_entries())
        return self.filter(has_compacted_log | has_log_entries)

    def has_compacted_log(self) -> "JobRunQuerySet":
        return self.exclude(log=None)

    def has_log_entries(self) -> "JobRunQuerySet":
        # Note: The self.exclude(log_entries=None) is very slow!
        return self.filter(pk__in=JobRunLogEntry.objects.values("run_id"))

    def compact_logs(self) -> int:
        """
        Compact logs of all job runs in the queryset.

        Return the amount of log entries that were compacted.
        """
        deleted_log_entries = 0
        for run in self.iterator(chunk_size=1000):
            deleted_log_entries += run.compact_logs()
        return deleted_log_entries

    def delete_logs(self) -> Tuple[int, int]:
        """
        Delete logs of all job runs in the queryset.

        Return the amounts of deleted compacted logs and log entries.
        """
        (total_deleted_logs, total_deleted_entries) = (0, 0)
        for run in self:
            (deleted_logs, deleted_entries) = run.delete_logs()
            total_deleted_logs += deleted_logs
            total_deleted_entries += deleted_entries
        return (total_deleted_logs, total_deleted_entries)

    def delete_with_logs(self) -> Tuple[int, int, int]:
        """
        Delete all job runs in the queryset with their logs.

        This effectively does a cascading delete, but still allows the
        field to be PROTECTed so that the job runs cannot be cascade
        deleted from Django admin etc.

        Return the amounts of deleted job run objects, compacted logs
        and log entries.
        """
        log_entries = JobRunLogEntry.objects.filter(run_id__in=self)
        (entries_deleted, _delete_info1) = log_entries.delete()
        logs = JobRunLog.objects.filter(run_id__in=self)
        (logs_deleted, _delete_info2) = logs.delete()
        (runs_deleted, _delete_info3) = self.delete()
        return (runs_deleted, logs_deleted, entries_deleted)


class JobRun(models.Model):
    """
    Instance of a job currently running or ran in the past.
    """

    job = models.ForeignKey(Job, on_delete=models.PROTECT, verbose_name=_("job"))
    pid = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("PID"),
        help_text=_(
            "Records the process id of the process, " "which is/was executing this job"
        ),
    )
    started_at = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("start time")
    )
    stopped_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("stop time")
    )
    exit_code = models.IntegerField(null=True, blank=True, verbose_name=_("exit code"))

    objects = JobRunQuerySet.as_manager()

    class Meta:
        verbose_name = _("job run")
        verbose_name_plural = _("job runs")

    def __str__(self) -> str:
        return f"{self.job} [{self.pid}] ({self.started_at:%Y-%m-%dT%H:%M})"

    def compact_logs(self) -> int:
        LOG.info("Compacting logs of %s", f"job run {self.pk} / {self}")
        with transaction.atomic():
            JobRunLog.create_for_run_if_not_exists(self)
            (deleted_entries, _delete_map) = self.log_entries.all().delete()
        return deleted_entries

    def delete_logs(self) -> Tuple[int, int]:
        me = f"job run {self.pk} / {self}"

        if self.log_entries.exists():
            LOG.info("Deleting log entries of %s", me)
            (deleted_entries, _delete_map) = self.log_entries.all().delete()
        else:
            deleted_entries = 0

        if hasattr(self, "log"):
            LOG.info("Deleting compacted log of %s", me)
            self.log.delete()
            deleted_log = 1
        else:
            deleted_log = 0

        return (deleted_log, deleted_entries)


class JobRunLogEntry(models.Model):
    """
    Entry in a log for a run of a job.

    A log is stored for each run of a job.  The log contains a several
    entries which are ordered by the "number" field in this model.  Each
    entry generally stores a line of output from either stdout or stderr
    stream.  The source stream is stored into the "kind" field.
    Additionally a creation timestamp is recorded to the "time" field.
    """

    run = models.ForeignKey(
        JobRun,
        on_delete=models.PROTECT,
        related_name="log_entries",
        verbose_name=_("run"),
    )
    kind = EnumIntegerField(LogEntryKind, verbose_name=_("kind"))
    line_number = models.IntegerField(verbose_name=_("line number"))
    number = models.IntegerField(verbose_name=_("number"))  # within line
    time = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("time")
    )
    text = models.TextField(null=False, blank=True, verbose_name=_("text"))

    class Meta:
        ordering = ("-run", "time", "id")
        verbose_name = _("log entry")
        verbose_name_plural = _("log entries")

    def __str__(self) -> str:
        return ugettext("{run_name}: {kind} entry {linenum}({number})").format(
            run_name=self.run,
            kind=self.kind,
            linenum=self.line_number,
            number=self.number,
        )


class JobRunLog(models.Model):
    run = models.OneToOneField(
        JobRun, on_delete=models.CASCADE, related_name="log", verbose_name=_("run"),
    )
    content = models.TextField(null=False, blank=True, verbose_name=_("content"))
    entry_data = TextJSONField(
        null=True,
        blank=True,
        verbose_name=_("log entry metadata"),
        help_text=(
            "Data that defines the location, timestamp and "
            "kind (stdout or stderr) of each log entry "
            "within the whole log content."
        ),
    )
    start = models.DateTimeField(
        db_index=True, verbose_name=_("timestamp of the first entry"),
    )
    end = models.DateTimeField(
        db_index=True, verbose_name=_("timestamp of the last entry"),
    )
    entry_count = models.IntegerField(verbose_name=_("total count of entries"))
    error_count = models.IntegerField(verbose_name=_("count of error entries"))

    class Meta:
        ordering = ("-start",)
        verbose_name = _("log")
        verbose_name_plural = _("logs")

    @classmethod
    def create_for_run_if_not_exists(cls, run: JobRun) -> Tuple[int, bool]:
        (job_run_log, created) = cls.objects.get_or_create(
            run=run,
            defaults=dict(
                start=run.started_at,
                end=(run.stopped_at or run.started_at),
                entry_count=0,
                error_count=0,
            ),
        )
        if not created:
            # Was already there, just return the pk and False
            return (job_run_log.pk, False)

        if not run.log_entries.exists():
            # No entries.  Nothing more to do
            return (job_run_log.pk, True)

        with connections[cls.objects.db].cursor() as cursor:
            cursor.execute("SELECT batchrun_compact_log_entries(%s)", (run.pk,))

        return (job_run_log.pk, True)

    def __iter__(self) -> Iterable[JobRunLogEntry]:
        compact_log = self.to_compact_log()
        line_number: Dict[LogEntryKind, int] = defaultdict(lambda: 1)
        number_within_line: Dict[LogEntryKind, int] = defaultdict(lambda: 1)
        for entry_datum in compact_log.iterate_entries():
            kind = entry_datum.kind
            yield JobRunLogEntry(
                run=self.run,
                kind=kind,
                line_number=line_number[kind],
                number=number_within_line[kind],
                time=entry_datum.time,
                text=entry_datum.text,
            )

            if entry_datum.text.endswith(LINE_END_CHARACTERS):
                line_number[kind] += 1
                number_within_line[kind] = 1
            else:
                number_within_line[kind] += 1

    def to_compact_log(self) -> CompactLog:
        return CompactLog(
            content=self.content,
            entry_data=self.entry_data,
            first_timestamp=self.start,
            last_timestamp=self.end,
            entry_count=self.entry_count,
            error_count=self.error_count,
        )


class JobRunQueueItemQuerySet(QuerySet["JobRunQueueItem"]):
    def to_run(self) -> "models.QuerySet[JobRunQueueItem]":
        return self.filter(scheduled_job__enabled=True, assigned_at=None)

    def remove_old_items(self, limit: Optional[datetime] = None) -> None:
        if limit is None:
            limit = utc_now() - GRACE_PERIOD_LENGTH
        self.filter(run_at__lt=limit).delete()

    def refresh(self) -> None:
        self.remove_old_items()

        for scheduled_job in ScheduledJob.objects.all():
            assert isinstance(scheduled_job, ScheduledJob)
            scheduled_job.update_run_queue()


class JobRunQueueItem(models.Model):
    run_at = models.DateTimeField(db_index=True, verbose_name=_("scheduled run time"))
    scheduled_job = models.ForeignKey(
        ScheduledJob,
        on_delete=models.CASCADE,
        related_name="run_queue_items",
        verbose_name=_("scheduled job"),
    )

    assigned_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("assignment time")
    )
    assignee_pid = models.IntegerField(
        null=True, blank=True, verbose_name=_("assignee process id (PID)")
    )

    objects = JobRunQueueItemQuerySet.as_manager()

    class Meta:
        ordering = ["run_at"]

    def __str__(self) -> str:
        return f"{self.run_at}: {self.scheduled_job}"
