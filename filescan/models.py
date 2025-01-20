import logging
import os
import uuid

import requests
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from filescan.enums import FileScanResult
from filescan.types import FileModelProtocol, PlattaClamAvResponse
from leasing.models.mixins import TimeStampedModel

logger = logging.getLogger(__name__)

# TODO batchrun to re-trigger scan after interrupted or failed scan processes?


def _get_filepath(file_model_instance: models.Model, file_field_name: str) -> str:
    """
    Resolves the file's path on the server, so that the correct file can be sent
    to scanning.
    """
    file_field = getattr(file_model_instance, file_field_name)
    return file_field.path


class FileScanStatus(TimeStampedModel):
    """
    In Finnish: Tiedoston virusskannauksen tila

    Tracks the scanning status of various file objects using a generic foreign key.

    It records the filepath, the time the scan was performed, and, whether the
    file was  marked for deletion due to detected virus or malware.
    """

    # Generic reference to a related file object.
    content_object = GenericForeignKey("content_type", "object_id")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
    )
    object_id = models.PositiveBigIntegerField()

    # Details of the file and its scanning status
    # TODO what to save here, from each of the file/attachment models?
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
    # rename field to something like "marked_for_deletion_at"
    file_deleted_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("deletion time")
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("error message"),
    )

    def scan_result(self) -> FileScanResult:
        """Determine the result of the virus scan."""
        if self.file_deleted_at is not None:
            return FileScanResult.UNSAFE
        elif self.error_message is not None:
            return FileScanResult.ERROR
        elif self.scanned_at is not None:
            return FileScanResult.SAFE
        else:
            return FileScanResult.PENDING

    class Meta:
        verbose_name = _("File Scan Status")
        verbose_name_plural = _("File Scan Statuses")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    recursive_get_related_skip_relations = [
        "content_type",
    ]


def schedule_file_for_virus_scanning(
    file_model_instance: models.Model, file_field_name: str
) -> FileScanStatus | None:
    """
    A factory function for creating FileScanStatus instances, and triggering a
    virus scan task.
    """
    error_message = None
    try:
        absolute_path = _get_filepath(file_model_instance, file_field_name)
    except AttributeError:
        absolute_path = None  # TODO logger
        error_message = f'Unable to find file field from "{file_field_name}"'

    file_scan_status = FileScanStatus.objects.create(
        content_object=file_model_instance,
        content_type=ContentType.objects.get_for_model(file_model_instance._meta.model),
        object_id=file_model_instance.pk,
        filepath=absolute_path,
        error_message=error_message,
    )

    if error_message is not None:
        return

    async_task(_scan_file_task, file_scan_status.pk)

    return file_scan_status


def _scan_file_task(scan_status_id: int) -> FileScanStatus | None:
    """
    Task to scan a file for viruses by calling an external service.

    If file is safe, no need for further actions.
    If file is unsafe, mark the file for deletion.
    """
    try:
        scan_status = FileScanStatus.objects.get(pk=scan_status_id)
        filepath = scan_status.filepath

        if not os.path.exists(filepath):
            _handle_error(filescan_obj=scan_status, text=f"File not found: {filepath}")
            return scan_status

        with open(filepath, "rb") as file:
            obfuscated_filename = str(uuid.uuid4())

            response = requests.post(
                settings.FILE_SCAN_SERVICE_URL,
                files={obfuscated_filename: file},
            )
            if not response.status_code == 200:
                _handle_error(
                    filescan_obj=scan_status,
                    text=f"Response from filescan service was not 200: {response.status_code}",
                )
                return scan_status

            response_dict: PlattaClamAvResponse = response.json()
            if not response_dict.get("success", False):
                _handle_error(
                    filescan_obj=scan_status,
                    text="Response from filescan service was not a success",
                )
                return scan_status

            response_result = response_dict.get("data", {}).get("result", [])[0]
            if response_result is None:
                _handle_error(
                    filescan_obj=scan_status,
                    text="Response from filescan service was empty",
                )
                return scan_status

            scan_status.scanned_at = timezone.now()

            if response_result["is_infected"]:
                # TODO when/where to delete the actual file?
                # Need to go through the file's model to remove the row or update deletion timestamp
                scan_status.file_deleted_at = timezone.now()

            scan_status.error_message = None
            scan_status.save()
            return scan_status

    except FileScanStatus.DoesNotExist:
        logger.error(f"FileScanStatus object with id {scan_status_id} does not exist")
        return None

    except Exception as e:
        _handle_error(filescan_obj=scan_status, text=f"An error occurred: {e}")
        return None


def _handle_error(filescan_obj: FileScanStatus, text: str) -> None:
    logger.error(text)
    filescan_obj.error_message = text
    filescan_obj.save()
    return
