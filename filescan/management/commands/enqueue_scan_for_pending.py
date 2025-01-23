import time

from django.core.management.base import BaseCommand
from django_q.tasks import async_task

from filescan.models import FileScanStatus, _scan_file_task


class Command(BaseCommand):
    """"""

    help = """Queue scanning for files that have not been scanned yet (PENDING).
    Can be a long running task, ensure your shell does not die during execution."""

    def handle(self, *args, **options):
        # Filter for FileScanResult.PENDING
        pending_scan_statuses = FileScanStatus.objects.filter(
            scanned_at__isnull=True,
            file_deleted_at__isnull=True,
        )
        pending_scan_status_count = pending_scan_statuses.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"About to queue scan for {pending_scan_status_count} files."
            )
        )
        batch_size = 10
        delay_between_batches = 300  # seconds

        batch = []
        for scan in pending_scan_statuses.iterator():
            batch.append(scan)
            if len(batch) == batch_size:
                self.process_batch(batch)
                batch = []
                time.sleep(delay_between_batches)

        self.stdout.write(self.style.SUCCESS("DONE"))

    def process_batch(self, batch):
        for scan in batch:
            async_task(
                _scan_file_task,
                scan.pk,
                task_name=f"FileScanStatus {scan.pk}",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Queued batch of {len(batch)} scans: {','.join([str(x.id) for x in batch])}"
            )
        )
