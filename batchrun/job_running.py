import codecs
import subprocess
import threading
from shutil import copyfileobj
from typing import BinaryIO, cast

from django import db

from ._times import utc_now
from .constants import LINE_END_CHARACTERS
from .enums import LogEntryKind
from .models import JobRun, JobRunLogEntry


def execute_job_run(job_run: JobRun) -> None:
    command = job_run.job.get_command_line()
    pipe = subprocess.Popen(
        command,
        bufsize=0,  # unbuffered
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    job_run.pid = pipe.pid
    job_run.save(update_fields=["pid"])

    stdout_collector_thread = OutputCollectorThread(
        job_run, LogEntryKind.STDOUT, cast(BinaryIO, pipe.stdout)
    )
    stderr_collector_thread = OutputCollectorThread(
        job_run, LogEntryKind.STDERR, cast(BinaryIO, pipe.stderr)
    )
    stdout_collector_thread.start()
    stderr_collector_thread.start()

    pipe.wait()

    job_run.stopped_at = utc_now()
    job_run.exit_code = pipe.returncode
    job_run.save(update_fields=["stopped_at", "exit_code"])

    stdout_collector_thread.join()
    stderr_collector_thread.join()


class OutputCollectorThread(threading.Thread):
    def __init__(self, job_run: JobRun, kind: LogEntryKind, stream: BinaryIO) -> None:
        self.log_writer = LogWriter(job_run, kind)
        self.stream = stream
        self._chunk_size = 4096  # read at most 4096 bytes at time
        super().__init__()

    def run(self) -> None:
        try:
            copyfileobj(self.stream, self.log_writer, self._chunk_size)
        finally:
            # Close the database connection to free up resources.  See
            # the comments from JobRunnerAndFollower.run.
            db.connection.close()


class LogWriter:
    def __init__(self, job_run: JobRun, kind: LogEntryKind) -> None:
        self.job_run = job_run
        self.kind = kind
        self.coding = "utf-8"
        self._line_number = 1
        self._number_within_line = 1
        decoder_class = codecs.getincrementaldecoder(self.coding)
        self._decoder = decoder_class(errors="backslashreplace")

    def write(self, data: bytes) -> int:
        timestamp = utc_now()
        text = self._decoder.decode(data)

        # Split the text to lines and store each in a separate record
        for line in text.splitlines(keepends=True):
            JobRunLogEntry.objects.create(
                run=self.job_run,
                kind=self.kind.value,
                line_number=self._line_number,
                number=self._number_within_line,
                time=timestamp,
                text=line,
            )
            if line.endswith(LINE_END_CHARACTERS):
                self._line_number += 1
                self._number_within_line = 1
            else:
                self._number_within_line += 1

        return len(data)
