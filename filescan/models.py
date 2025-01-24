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
from filescan.types import PlattaClamAvResponse, PlattaClamAvResult
from leasing.models.mixins import TimeStampedModel
from utils.models.fields import PrivateFieldFile

logger = logging.getLogger(__name__)


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
    field_file: PrivateFieldFile = getattr(file_model_instance, file_field_name)
    return field_file.path


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
            _handle_error(scan_status, f"File not found: {filepath}")
            return scan_status

        with open(filepath, "rb") as file:
            obfuscated_filename = str(uuid.uuid4())

            response = requests.post(
                settings.FILE_SCAN_SERVICE_URL,
                files={"FILES": (obfuscated_filename, file)},
            )
            if not response.status_code == 200:
                _handle_error(
                    scan_status,
                    f"Response from filescan service was not 200: {response.status_code}",
                )
                return scan_status

            response_dict: PlattaClamAvResponse = response.json()
            if not response_dict.get("success", False):
                _handle_error(
                    scan_status,
                    f"Scanning service failed: {response_dict}",
                )
                return scan_status

            try:
                scanning_result = response_dict.get("data", {}).get("result", [])[0]
            except TypeError:
                _handle_error(
                    scan_status,
                    f"Response from filescan service did not contain a result: {response_dict}",
                )
                return scan_status

            return _handle_scanning_result(scan_status, scanning_result)

    except Exception as e:
        _handle_error(scan_status, f"An error occurred: {e}")


def _handle_error(scan_status: FileScanStatus, text: str) -> None:
    logger.error(text)
    scan_status.error_message = text
    scan_status.save()


def _handle_scanning_result(
    scan_status: FileScanStatus, scanning_result: PlattaClamAvResult
) -> FileScanStatus:
    scan_status.scanned_at = timezone.now()

    if scanning_result["is_infected"]:
        _delete_infected_file(scan_status)
        scan_status.file_deleted_at = timezone.now()

    scan_status.error_message = None
    scan_status.save()
    return scan_status


def _delete_infected_file(scan_status: FileScanStatus) -> None:
    file_object: models.Model | None = scan_status.content_object
    if file_object is None:
        raise AttributeError

    field_file: PrivateFieldFile = getattr(
        file_object, scan_status.filefield_field_name
    )
    field_file.delete()
    file_object.save()

    scan_status.file_deleted_at = timezone.now()
    scan_status.save()
