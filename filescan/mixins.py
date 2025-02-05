from django.conf import settings

from utils.models.fields import PrivateFileField


class FileScanMixin:
    """
    On save(), if file scanning feature flag FLAG_FILE_SCAN is enabled, queues
    an asynchronous virus/malware scan for the file.
    """

    def save(self, *args, skip_virus_scan: bool = False, **kwargs):
        super().save(*args, **kwargs)

        file_scans_are_enabled = getattr(settings, "FLAG_FILE_SCAN")
        if (
            file_scans_are_enabled is True
            and skip_virus_scan is False
            and not _is_safedelete_delete_action(kwargs)
        ):
            from filescan.models import schedule_file_for_virus_scanning

            for field in self._meta.fields:
                if isinstance(field, PrivateFileField):
                    fieldfile = getattr(self, field.attname)
                    if fieldfile:
                        schedule_file_for_virus_scanning(
                            file_model_instance=self, file_field_name=field.attname
                        )


def _is_safedelete_delete_action(keyword_arguments: dict) -> bool:
    """
    safedelete.models.SafeDelete runs an additional save() during delete
    process, and triggering another filescan is not desirable in that case.
    """
    return "keep_deleted" in keyword_arguments.keys()
