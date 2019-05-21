from django.contrib import admin

from .admin_utils import PreciseTimeFormatter, ReadOnlyAdmin
from .models import (
    Command, Job, JobRun, JobRunLogEntry, JobRunQueueItem, ScheduledJob,
    Timezone)


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ['type', 'name']
    exclude = ['parameters']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['name', 'comment', 'command']


@admin.register(JobRun)
class JobRunAdmin(ReadOnlyAdmin):
    date_hierarchy = 'started_at'
    list_display = ['started_at_p', 'stopped_at_p', 'job', 'exit_code']
    list_filter = ['exit_code']

    started_at_p = PreciseTimeFormatter(JobRun, 'started_at')
    stopped_at_p = PreciseTimeFormatter(JobRun, 'stopped_at')


@admin.register(JobRunLogEntry)
class JobRunLogEntryAdmin(ReadOnlyAdmin):
    date_hierarchy = 'time'
    list_display = ['time_p', 'run', 'kind', 'line_number', 'number', 'text']
    list_filter = ['kind']

    time_p = PreciseTimeFormatter(JobRunLogEntry, 'time')


@admin.register(JobRunQueueItem)
class JobRunQueueItemAdmin(ReadOnlyAdmin):
    date_hierarchy = 'run_at'
    list_display = ['run_at', 'scheduled_job', 'assigned_at', 'assignee_pid']


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    list_display = [
        'job', 'enabled', 'comment',
        'years', 'months', 'days_of_month', 'weekdays', 'hours', 'minutes',
        'timezone',
    ]
    list_filter = ['enabled']


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    pass
