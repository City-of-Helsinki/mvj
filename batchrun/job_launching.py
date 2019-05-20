import multiprocessing
import subprocess
import sys

import daemon

from .management.commands import batchrun_execute_job_run
from .models import Job, JobRun
from .utils import get_django_manage_py


def run_job(job: Job) -> JobRun:
    """
    Run given job and store its output logs to database.

    The job is run asynchronously, so it is probably still running when
    this function returns.

    The output of the job is logged to database while it is accumulated
    from the stdout and stderr streams.  The logs can be accessed through the
    returned JobRun object with `job_run.log_entries.all()`.

    The exit code and stopping time of the job is stored to the JobRun
    object as soon as the job finishes.  Use `job_run.refresh_from_db()`
    to make them visible.

    :return: JobRun object of the stared job.
    """
    job_run = JobRun.objects.create(job=job)
    launcher = JobRunLauncher(job_run)
    launcher.start()
    launcher.join()
    return job_run


class JobRunLauncher(multiprocessing.Process):
    def __init__(self, job_run: JobRun) -> None:
        self._manage_py = get_django_manage_py()
        self.job_run = job_run
        super().__init__()

    def run(self) -> None:
        name = batchrun_execute_job_run.__name__.rsplit('.', 1)[-1]
        command = [sys.executable, self._manage_py, name, str(self.job_run.pk)]
        with daemon.DaemonContext(umask=0o022, detach_process=True):
            subprocess.run(command)
