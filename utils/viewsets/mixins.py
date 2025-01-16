from typing import NoReturn

from django.conf import settings
from django.http import FileResponse
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


class FileDownloadMixin:
    @action(methods=["get"], detail=True)
    def download(self, request, pk=None, file_field: str | None = None):
        obj = self.get_object()
        if file_field is not None:
            filename = getattr(obj, file_field).name
        else:
            filename = obj.file.name
        filepath = "/".join([settings.MEDIA_ROOT, filename])
        response = FileResponse(open(filepath, "rb"), as_attachment=True)

        return response


class FileMixin:
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

    def create(self, request, *args, **kwargs):
        files: MultiValueDict = getattr(request, "FILES")
        if files and len(files) > 0:
            self._validate_file_extensions(files)

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        files: MultiValueDict = getattr(request, "FILES")
        if files and len(files) > 0:
            self._validate_file_extensions(files)

        return super().update(request, *args, **kwargs)

    @action(methods=["get"], detail=True)
    def download(self, request, pk=None, file_field: str | None = None):
        return FileDownloadMixin.download(self, request, pk, file_field=file_field)
