from django.conf import settings
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


class FileDownloadMixin:
    @action(methods=["get"], detail=True)
    def download(self, request, pk=None):
        obj = self.get_object()

        filename = "/".join([settings.MEDIA_ROOT, obj.file.name])
        response = FileResponse(open(filename, "rb"), as_attachment=True)

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
    def download(self, request, pk=None):
        return FileDownloadMixin.download(self, request, pk)
