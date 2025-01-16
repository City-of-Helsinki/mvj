import logging
import os

import requests
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from filescan.enums import FileScanResult, FileScanStatusContentType
from filescan.types import PlattaClamAvResponse
from leasing.models.mixins import TimeStampedModel

logger = logging.getLogger(__name__)

# TODO batchrun to re-trigger scan after interrupted or failed scan processes?

# TODO factory function for easy creation of FileScanStatus instances, to be called
# in the attachment/file model save methods.


class FileScanStatus(TimeStampedModel):
    """
    In Finnish: Tiedoston virusskannauksen tila

    Tracks the scanning status of various file objects using a generic foreign key.

    It records the filepath, the time the scan was performed, and, whether the
    file was  marked for deletion due to detected virus or malware.
    """

    # Generic reference to a related file object.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        limit_choices_to={"model__in": FileScanStatusContentType.values()},
    )
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # Details of the file and its scanning status
    filepath = models.CharField(
        max_length=255,
        verbose_name=_("filepath"),
        help_text="Filepath for preservation even after the original row has "
        "been deleted from a table referenced by the generic foreign key.",
    )
    scanned_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("scan time")
    )
    # TODO if the target file is not actually deleted when this is updated,
    # rename field to something like "marked_for_deletion"
    deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("deletion time")
    )
    error_message = models.CharField(
        null=True,
        blank=True,
        max_length=511,
        verbose_name=_("error message"),
    )

    def scan_result(self) -> FileScanResult:
        """Determine the result of the virus scan."""
        if self.deleted_at:
            return FileScanResult.UNSAFE
        elif self.error_message:
            return FileScanResult.ERROR
        elif self.scanned_at:
            return FileScanResult.SAFE
        else:
            return FileScanResult.PENDING

    def save(self, *args, **kwargs):
        """
        Triggers the async file scan process.
        """
        super().save(*args, **kwargs)
        async_task("filescan.tasks.scan_file_task", self.pk)

    class Meta:
        verbose_name = _("File Scan Status")
        verbose_name_plural = _("File Scan Statuses")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    recursive_get_related_skip_relations = [
        "content_type",
    ]


def scan_file_task(scan_status_id: int):
    """
    Task to scan a file for viruses by calling an external service.

    If file is safe, no need for further actions.
    If file is unsafe, mark the file for deletion.
    """
    try:
        scan_status = FileScanStatus.objects.get(pk=scan_status_id)
        filepath = scan_status.filepath

        file_path = os.path.join(settings.PRIVATE_FILES_LOCATION, filepath)

        if not os.path.exists(file_path):
            handle_error(filescan_obj=scan_status, text=f"File not found: {file_path}")
            return

        # TODO disguise the filepath before scan?
        # TODO remove metadata before scan?
        with open(file_path, "rb") as file:
            response = requests.post(
                settings.FILE_SCAN_SERVICE_URL,
                files={"FILES": file},
            )
            if not response.status_code == 200:
                handle_error(
                    filescan_obj=scan_status,
                    text=f"Response from filescan service was not 200: {response.status_code}",
                )
                return

            response_dict: PlattaClamAvResponse = response.json()
            if not response_dict.get("success"):
                handle_error(
                    filescan_obj=scan_status,
                    text="Response from filescan service was not a success",
                )
                return

            response_result = response_dict.get("data", {}).get("result", [])[0]
            if response_result is None:
                handle_error(
                    filescan_obj=scan_status,
                    text="Response from filescan service was empty",
                )
                return

            scan_status.scanned_at = timezone.now()

            if response_result["is_infected"]:
                # TODO when/where to delete the actual file?
                # Need to go through the file's model to remove the row or update deletion timestamp
                scan_status.deleted_at = timezone.now()

            scan_status.error_message = None
            scan_status.save()

    except FileScanStatus.DoesNotExist:
        logger.error(f"FileScanStatus object with id {scan_status_id} does not exist")
        return

    except Exception as e:
        handle_error(filescan_obj=scan_status, text=f"An error occurred: {e}")
        return


def handle_error(filescan_obj: FileScanStatus, text: str) -> None:
    logger.error(text)
    filescan_obj.error_message = text
    filescan_obj.save()
    return
