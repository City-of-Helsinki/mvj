import sys
import threading
from unittest.mock import MagicMock

import pytest
from django import db
from django.db import OperationalError

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
SCRIPT_RETRY_TEST = "print('hello from retry test')"
SCRIPT_DJANGO_BASELINE = "print('baseline connection behavior')"
SCRIPT_DELAYED_STREAM_OUTPUT = (
    "import sys, time; "
    "print('first'); "
    "sys.stdout.flush(); "
    "time.sleep(0.05); "
    "print('second'); "
    "print('err', file=sys.stderr)"
)


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
def test_execute_job_run_retries_final_save_after_operational_error(
    job_run_factory,
    monkeypatch: pytest.MonkeyPatch,
):
    job_run = _create_job_run_for_python_code(job_run_factory, SCRIPT_RETRY_TEST)
    close_old_connections = MagicMock()

    original_save = job_run.save
    save_state = {"final_save_attempt_count": 0}

    def flaky_save(*args, **kwargs):
        if kwargs.get("update_fields") == FINAL_SAVE_FIELDS:
            save_state["final_save_attempt_count"] += 1
            if save_state["final_save_attempt_count"] == 1:
                raise OperationalError("simulated idle timeout")
        return original_save(*args, **kwargs)

    monkeypatch.setattr(job_run, "save", flaky_save)
    monkeypatch.setattr(
        "batchrun.job_running.db.close_old_connections", close_old_connections
    )

    execute_job_run(job_run)
    job_run.refresh_from_db()

    assert save_state["final_save_attempt_count"] == 2
    close_old_connections.assert_called_once_with()
    assert job_run.exit_code == 0
    assert job_run.stopped_at is not None


@pytest.mark.django_db(transaction=True)
def test_django_query_and_write_work_after_explicit_connection_close(job_run_factory):
    # Regression guard for a framework-level assumption used by execute_job_run:
    # after explicitly closing db.connection, Django must transparently open a new
    # connection on the next ORM query so subsequent reads/writes still succeed.
    # This behavior is critical for our idle-timeout mitigation and we keep this
    # test to detect upstream Django behavior changes early.
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


@pytest.mark.django_db(transaction=True)
def test_log_entry_writes_continue_after_main_thread_connection_close(
    job_run_factory,
    monkeypatch: pytest.MonkeyPatch,
):
    job_run = _create_job_run_for_python_code(
        job_run_factory, SCRIPT_DELAYED_STREAM_OUTPUT
    )

    main_close_called = threading.Event()
    saw_log_write_after_main_close = threading.Event()

    original_close = db.connection.close

    def close_spy() -> None:
        if threading.current_thread() is threading.main_thread():
            main_close_called.set()
        original_close()

    original_create = JobRunLogEntry.objects.create

    def create_spy(*args, **kwargs):
        if (
            main_close_called.is_set()
            and threading.current_thread() is not threading.main_thread()
        ):
            saw_log_write_after_main_close.set()
        return original_create(*args, **kwargs)

    monkeypatch.setattr("batchrun.job_running.db.connection.close", close_spy)
    monkeypatch.setattr(JobRunLogEntry.objects, "create", create_spy)

    execute_job_run(job_run)

    assert main_close_called.is_set()
    assert saw_log_write_after_main_close.is_set()
