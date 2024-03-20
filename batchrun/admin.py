from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import escape as html_escape
from django.utils.safestring import mark_safe
from rangefilter.filters import DateRangeFilter

from .admin_utils import PreciseTimeFormatter, ReadOnlyAdmin, WithDownloadableContent
from .models import (
    Command,
    Job,
    JobHistoryRetentionPolicy,
    JobRun,
    JobRunLog,
    JobRunLogEntry,
    JobRunQueueItem,
    ScheduledJob,
    Timezone,
)


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ["type", "name"]
    exclude = ["parameters"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["name", "comment", "command"]


@admin.register(JobHistoryRetentionPolicy)
class JobHistoryRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = [
        "identifier",
        "compact_logs_delay",
        "delete_logs_delay",
        "delete_run_delay",
    ]


class JobRunLogEntryInline(admin.TabularInline):
    model = JobRunLogEntry
    show_change_link = True


@admin.register(JobRun)
class JobRunAdmin(ReadOnlyAdmin):
    date_hierarchy = "started_at"
    inlines = [JobRunLogEntryInline]
    list_display = ["started_at_p", "stopped_at_p", "job", "exit_code"]
    list_filter = ("started_at", ("started_at", DateRangeFilter), "job", "exit_code")
    # auto_now_add_fields don't show even in readonlyadmin.
    # Therefore we'll add all the fields by hand in a suitable order
    readonly_fields = ("job", "pid", "started_at_p", "stopped_at_p", "exit_code")
    search_fields = ["log_entries__text"]
    exclude = ["stopped_at"]

    started_at_p = PreciseTimeFormatter(JobRun, "started_at")
    stopped_at_p = PreciseTimeFormatter(JobRun, "stopped_at")


@admin.register(JobRunLogEntry)
class JobRunLogEntryAdmin(ReadOnlyAdmin):
    date_hierarchy = "time"
    list_display = ["time_p", "run", "kind", "line_number", "number", "text"]
    list_filter = ["kind", "run__job"]
    readonly_fields = ("time_p", "run", "kind", "line_number", "number", "text")

    time_p = PreciseTimeFormatter(JobRunLogEntry, "time")


@admin.register(JobRunLog)
class JobRunLogAdmin(WithDownloadableContent, ReadOnlyAdmin):
    date_hierarchy = "start"
    list_display = ["run", "start_p", "end_p", "entry_count", "error_count"]
    list_filter = ["run__job", "run__exit_code"]
    readonly_fields = [
        "run",
        "start_p",
        "end_p",
        "entry_count",
        "error_count",
        "download_content",
        "content_preview",
    ]
    search_fields = ["content"]
    exclude = ["content", "entry_data", "start", "end"]

    start_p = PreciseTimeFormatter(JobRunLog, "start")
    end_p = PreciseTimeFormatter(JobRunLog, "end")

    def get_queryset(self, request: HttpRequest) -> "QuerySet[JobRunLog]":
        qs = super().get_queryset(request)
        return qs.defer("content", "entry_data")

    def content_preview(self, obj: JobRunLog, max_length: int = 20000) -> str:
        to_elide = len(obj.content) - max_length
        if to_elide <= 0:
            return obj.content
        half_len = max_length // 2
        lines1 = obj.content[:half_len].splitlines()
        lines2 = obj.content[-half_len:].splitlines()
        all_lines = (
            [f"{html_escape(x)}<br>" for x in lines1]
            + ["<br><i>... ELIDED ...</i><br><br>"]
            + [f"{html_escape(x)}<br>" for x in lines2]
            + [f"<br><b>{to_elide} CHARACTERS ELIDED. DOWNLOAD TO GET ALL</b>"]
        )

        return mark_safe("".join(all_lines))

    def get_downloadable_content(self, obj: JobRunLog) -> str:
        return obj.content

    def get_downloadable_content_filename(self, obj: JobRunLog) -> str:
        return f"{obj.run.started_at:%Y-%m-%d_%H%M_%s}_run{obj.run.id}_log.txt"


@admin.register(JobRunQueueItem)
class JobRunQueueItemAdmin(ReadOnlyAdmin):
    date_hierarchy = "run_at"
    list_display = ["run_at", "scheduled_job", "assigned_at", "assignee_pid"]


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    list_display = [
        "job",
        "enabled",
        "comment",
        "years",
        "months",
        "days_of_month",
        "weekdays",
        "hours",
        "minutes",
        "timezone",
    ]
    list_filter = ["enabled"]


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    pass
