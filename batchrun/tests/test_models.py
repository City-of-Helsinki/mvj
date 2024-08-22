from datetime import timedelta

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from batchrun.models import JobRun


@pytest.mark.django_db
def test_jobrunlog_delete(job_run_log_factory):
    jobrunlog_entry_dict = job_run_log_factory(
        start=timezone.now() - timedelta(hours=1),
        end=timezone.now(),
        entry_count=100,
        error_count=1,
        content="test content",
        entry_data={"test": "data"},
    )

    jobrun_dict: JobRun = JobRun.objects.get(pk=jobrunlog_entry_dict.run.pk)
    assert jobrun_dict.log is not None
    jobrun_dict.delete_logs()
    jobrun_dict.refresh_from_db()
    with pytest.raises(ObjectDoesNotExist):
        jobrun_dict.log

    jobrunlog_entry_json = job_run_log_factory(
        start=timezone.now() - timedelta(hours=1),
        end=timezone.now(),
        entry_count=100,
        error_count=1,
        content="test content",
        entry_data='{"test": "data"}',
    )

    jobrun_json: JobRun = JobRun.objects.get(pk=jobrunlog_entry_json.run.pk)
    assert jobrun_json.log is not None
    jobrun_json.delete_logs()
    jobrun_json.refresh_from_db()
    with pytest.raises(ObjectDoesNotExist):
        jobrun_json.log
