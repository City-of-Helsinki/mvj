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
from filescan.types import PlattaClamAvResponse
from leasing.models.mixins import TimeStampedModel
from utils.models.fields import PrivateFieldFile

logger = logging.getLogger(__name__)

# TODO batchrun to re-trigger scan after interrupted or failed scan processes?


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

    filefield_field_name = models.CharField(
        null=False,
        blank=False,
        help_text="Name of the column of the content object's FileField",
    )

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
        elif self.error_message:
            return FileScanResult.ERROR
        elif self.scanned_at is not None:
            return FileScanResult.SAFE
        else:
            return FileScanResult.PENDING

    @staticmethod
    def is_file_scanned_and_safe(fieldfile_instance: PrivateFieldFile) -> bool:
        if settings.FLAG_FILE_SCAN is True:
            from filescan.models import FileScanStatus

            content_type = ContentType.objects.get_for_model(fieldfile_instance)
            scan_status = (
                FileScanStatus.objects.filter(
                    content_type=content_type,
                    object_id=fieldfile_instance.pk,
                )
                .order_by("id")
                .last()
            )
            if scan_status is None:
                return False

            scan_result = scan_status.scan_result()
            is_file_scanned_and_safe = scan_result == FileScanResult.SAFE
            return is_file_scanned_and_safe

        return True

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
        absolute_path = None
        error_message = f'Unable to find file field from "{file_field_name}"'

    file_scan_status = FileScanStatus.objects.create(
        content_object=file_model_instance,
        content_type=ContentType.objects.get_for_model(file_model_instance._meta.model),
        object_id=file_model_instance.pk,
        filepath=absolute_path,
        filefield_field_name=file_field_name,
        error_message=error_message,
    )

    if error_message is not None:
        _handle_error(file_scan_status, error_message)
        return file_scan_status

    async_task(_scan_file_task, file_scan_status.pk)

    return file_scan_status


def _get_filepath(file_model_instance: models.Model, file_field_name: str) -> str:
    file_field = getattr(file_model_instance, file_field_name)
    return file_field.path


def _scan_file_task(scan_status_id: int) -> FileScanStatus | None:
    """
    Task to scan a file for viruses by calling an external service.

    If file is safe, no need for further actions.
    If file is unsafe, mark the file for deletion.
    """
    try:
        scan_status = FileScanStatus.objects.get(pk=scan_status_id)
    except FileScanStatus.DoesNotExist:
        logger.error(f"FileScanStatus object with id {scan_status_id} does not exist")
        return None

    try:
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
                _delete_file(scan_status)
                scan_status.file_deleted_at = timezone.now()

            scan_status.error_message = None
            scan_status.save()
            return scan_status

    except Exception as e:
        _handle_error(filescan_obj=scan_status, text=f"An error occurred: {e}")


def _handle_error(filescan_obj: FileScanStatus, text: str) -> None:
    logger.error(text)
    filescan_obj.error_message = text
    filescan_obj.save()


def _delete_file(filescan_obj: FileScanStatus) -> None:
    file_object = filescan_obj.content_object
    filefield = getattr(file_object, filescan_obj.filefield_field_name)
    filefield.delete()
    file_object.save()

    filescan_obj.file_deleted_at = timezone.now()
    filescan_obj.save()
