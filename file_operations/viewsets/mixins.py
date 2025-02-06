from typing import NoReturn

from django.conf import settings
from django.http import FileResponse
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from file_operations.errors import FileScanError, FileScanPendingError, FileUnsafeError
from file_operations.private_files import PrivateFieldFile, PrivateFileField


class FileScanMixin:
    """
    On save(), if file scanning feature flag FLAG_FILE_SCAN is enabled, queues
    an asynchronous virus/malware scan for the file.
    """

    def save(self, *args, skip_virus_scan: bool = False, **kwargs):
        super().save(*args, **kwargs)

        file_scans_are_enabled = getattr(settings, "FLAG_FILE_SCAN", False) is True
        if (
            file_scans_are_enabled is True
            and skip_virus_scan is False
            and not _is_safedelete_delete_action(kwargs)
        ):
            from file_operations.models.filescan import schedule_file_for_virus_scanning

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


MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class FileDownloadMixin:
    # We import "action" in each class separately, because otherwise this import
    # creates a circular dependency through rest_framework.decorators and
    # leasing.metadata
    from rest_framework.decorators import action

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None, file_field: str | None = None):
        if file_field is None:
            raise ValueError(
                "file_field is required in order to utilize FileDownloadMixin"
            )

        obj = self.get_object()
        private_fieldfile: PrivateFieldFile = getattr(obj, file_field)

        try:
            file = private_fieldfile.open("rb")
            return FileResponse(file, as_attachment=True)
        except (FileScanPendingError, FileUnsafeError, FileScanError) as e:
            return get_filescan_error_response(e)


def get_filescan_error_response(error: Exception) -> Response:
    try:
        raise error
    except FileScanPendingError:
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data={
                "error": _(
                    "File has not yet been scanned for viruses, and is unsafe to download at this time."
                )
            },
        )
    except FileUnsafeError:
        return Response(
            status=status.HTTP_410_GONE,
            data={
                "error": _(
                    "File was found to contain virus or malware, and the file has been deleted."
                )
            },
        )
    except FileScanError:
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data={
                "error": _(
                    "File scan failed. "
                    "File is unsafe to download before it has been successfully scanned for viruses and malware."
                )
            },
        )
    except Exception:
        error_str = str(error)
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data={
                "error": _(f"Unknown error related to virus scanning: '{error_str}'")
            },
        )


class FileMixin:
    from rest_framework.decorators import action

    def create(self, request, *args, **kwargs):
        """Use the Class.serializer_class after the creation for returning the saved data.
        Instead of a different serializer used in 'create' action."""
        if not self.serializer_class:
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        read_serializer = self.serializer_class(
            serializer.instance, context=serializer.context
        )

        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """Use the Class.serializer_class after update for returning the saved data.
        Instead of a different serializer used in 'update' action."""
        if not self.serializer_class:
            return super().create(request, *args, **kwargs)

        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        read_serializer = self.serializer_class(
            serializer.instance, context=serializer.context
        )

        return Response(read_serializer.data)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None, file_field: str | None = None):
        return FileDownloadMixin.download(self, request, pk, file_field=file_field)


class FileExtensionFileMixin:
    from rest_framework.decorators import action

    @staticmethod
    def get_allowed_extensions() -> list[str]:
        # If you make changes to the list of allowed extensions,
        # make sure you update those also in the front-end.
        document_types = [
            "pdf",
            "csv",
            "txt",
            # Word
            "doc",
            "docx",
            "xls",
            "xlsx",
            "ppt",
            "pptx",
            # OpenOffice/LibreOffice
            "odt",
            "fodt",
            "ods",
            "fods",
        ]
        image_types = [
            "jpg",
            "jpeg",
            "jxl",
            "png",
            "gif",
            "tiff",
            "bmp",
            "svg",
            "webp",
        ]
        return document_types + image_types

    def _validate_file_extensions(self, files: MultiValueDict) -> NoReturn:
        """
        Validate file extensions of uploaded files from the file extension.
        Does not validate the the file type from the first bytes of the tile,
        nor does it validate the content type / mimetype of the file.

        Raises:
            ValidationError: If a file does not have an extension or if the extension is not allowed.
        """

        allowed_extensions = self.get_allowed_extensions()
        for file in files.values():
            if "." not in file.name:
                raise ValidationError(
                    _(f"File '{file.name}' does not have an extension.")
                )

            ext = file.name.split(".")[-1]
            if ext not in allowed_extensions:
                raise ValidationError(_(f"File extension '.{ext}' is not allowed."))

    def _validate_file_size(self, files: MultiValueDict) -> NoReturn:
        """
        Validate that the size of files do not exceed set maximum size.

        Raises:
            ValidationError: If a file is too large in size.
        """
        for file in files.values():
            if file.size > MAX_FILE_SIZE_BYTES:
                raise ValidationError(
                    _(
                        f"File '{file.name}' exceeds maximum file size of {MAX_FILE_SIZE_MB} MB."
                    )
                )

    def create(self, request, *args, **kwargs):
        files: MultiValueDict = getattr(request, "FILES")
        if files and len(files) > 0:
            self._validate_file_extensions(files)
            self._validate_file_size(files)

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        files: MultiValueDict = getattr(request, "FILES")
        if files and len(files) > 0:
            self._validate_file_extensions(files)
            self._validate_file_size(files)

        return super().update(request, *args, **kwargs)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None, file_field: str | None = None):
        return FileDownloadMixin.download(self, request, pk, file_field=file_field)
