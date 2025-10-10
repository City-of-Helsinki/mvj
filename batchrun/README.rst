batchrun - App for scheduling and running batch jobs
====================================================

Implements batch running functionality as a Django app.

Scheduled Jobs
---------------------------

Scheduled jobs and the run logs are stored into database via Django
models.

The scheduled jobs can be managed via Django Admin.

Run logs
--------------

There are two tables for run logs:

- batchrun_jobrunlogentry (class JobRunLogEntry)
- batchrun_jobrunlog (class JobRunLog)

A JobRunLogEntry is a single logged line of output (stdout or stderr).
After the retention period ends (for example 14 days), they are compacted into a
single JobRunLog row, and deleted from this table by the management command
`batchrun_log_rotate`.

A JobRunLog is a single run of a scheduled job. Because they are only created
from log entries 14 days after the actual date of the run, don't be alarmed when
you don't see last two weeks' runlogs in the table.

See JobHistoryRetentionPolicy for more information about cleaning schedules.

The run logs are visible in the Django Admin, and in addition there is
an API end point for listing them.

How It Works
------------

Main program for handling the job scheduling is implemented as a
management command "batchrun_scheduler".  It must be always running.

 * The main function of the `batchrun_scheduler` command is in
   `batchrun.scheduler.run_scheduler_loop`.

 * The scheduler will launch the scheduled jobs as new processes via
   `job_launching.run_job` function.  Which in turn runs the job via a
   management command `batchrun_execute_job_run` in daemon context
   (detaching the stdin, stdout and stderr, detaching from the process
   group, etc.).  This means that jobs are run to their completion even
   if the scheduler is terminated while they are running.

 * The `batchrun_execute_job_run` command is running the job via
   `job_running.execute_job_run` which then logs the progress of the
   command to the database: its stdout, stderr and finally the exit code
   and stopping timestamp.

Scheduling Rules
----------------

Scheduling rules are implemented in `scheduling` module.  Their API is
the `RecurrenceRule` class.  Such rule can be created with
`RecurrenceRule.create` function and then its events can be iterated
with the `RecurrenceRule.get_next_events` method.

Scheduling rules are defined by the following attributes:

  * timezone
  * years
  * months
  * days_of_month
  * weekdays
  * hours
  * minutes

The timezone field defines the timezone for the values in the other
fields.  It should be a timezone name like ``Europe/Helsinki``.  All
other fields should be strings which specify a single integer or a set
of integers with a so called integer set specifier syntax.  This syntax
allows expressions like ``2-15``, ``1,4,7-5``, or ``*/3`` to be used for
definining the value span of the field.
