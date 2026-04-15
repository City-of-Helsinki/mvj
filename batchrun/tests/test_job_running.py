import sys

import pytest
from django import db

from batchrun.enums import CommandType, LogEntryKind
from batchrun.job_running import execute_job_run
from batchrun.models import JobRun, JobRunLogEntry

FINAL_SAVE_FIELDS = ["stopped_at", "exit_code"]

SCRIPT_OUT_ERR_EXIT_3 = (
    "import sys; "
    "print('out-line'); "
    "print('err-line', file=sys.stderr); "
    "sys.exit(3)"
)
SCRIPT_DJANGO_BASELINE = "print('baseline connection behavior')"


def _create_job_run_for_python_code(job_run_factory, code: str) -> JobRun:
    """Create a JobRun whose command executes the given Python source via `python -c`."""
    return job_run_factory(
        job__command__type=CommandType.EXECUTABLE,
        job__command__name=sys.executable,
        job__command__parameter_format_string="-c '{code}'",
        job__arguments={"code": code},
    )


@pytest.mark.django_db(transaction=True)
def test_execute_job_run_allows_db_reads_and_writes_after_connection_close(
    job_run_factory,
):
    job_run = _create_job_run_for_python_code(
        job_run_factory,
        SCRIPT_OUT_ERR_EXIT_3,
    )

    execute_job_run(job_run)

    job_run.refresh_from_db()

    assert job_run.pid is not None
    assert job_run.exit_code == 3
    assert job_run.stopped_at is not None

    log_entries = JobRunLogEntry.objects.filter(run=job_run)
    assert log_entries.exists()
    assert log_entries.filter(text__contains="out-line").exists()
    assert log_entries.filter(text__contains="err-line").exists()
    kinds = set(log_entries.values_list("kind", flat=True))
    assert LogEntryKind.STDOUT.value in kinds
    assert LogEntryKind.STDERR.value in kinds

    # A write query after the forced close should also work normally.
    job_run.exit_code = 99
    job_run.save(update_fields=["exit_code"])
    job_run.refresh_from_db()
    assert job_run.exit_code == 99


@pytest.mark.django_db(transaction=True)
def test_django_query_and_write_work_after_explicit_connection_close(job_run_factory):
    """
    Regression guard for a framework-level assumption used by execute_job_run:
    after explicitly closing db.connection, Django must transparently open a new
    connection on the next ORM query so subsequent reads/writes still succeed.
    behavior is critical for our idle-timeout mitigation and we keep this
    to detect upstream Django behavior changes early.
    """
    job_run = _create_job_run_for_python_code(job_run_factory, SCRIPT_DJANGO_BASELINE)

    # Ensure an open DB connection exists, then close it explicitly.
    db.connection.ensure_connection()
    assert db.connection.connection is not None
    db.connection.close()
    assert db.connection.connection is None

    # The next query should transparently reopen the connection.
    fetched = JobRun.objects.get(pk=job_run.pk)
    assert fetched.pk == job_run.pk
    assert db.connection.connection is not None

    # Writes should continue to work after reconnect.
    fetched.exit_code = 123
    fetched.save(update_fields=["exit_code"])
    fetched.refresh_from_db()
    assert fetched.exit_code == 123
