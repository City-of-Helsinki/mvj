import json
import os

from auditlog.middleware import AuditlogMiddleware
from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class AuditLogMixin:
    def initial(self, request, *args, **kwargs):
        # We need to process logged in user again because Django Rest
        # Framework handles authentication after the
        # AuditLogMiddleware.
        AuditlogMiddleware().process_request(request)
        return super().initial(request, *args, **kwargs)


class AtomicTransactionMixin:
    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AtomicTransactionModelViewSet(AtomicTransactionMixin, viewsets.ModelViewSet):
    """Viewset that combines AtomicTransactionMixin and rest_framework.viewsets.ModelViewSet"""


class MultiPartJsonParser(parsers.MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type=media_type, parser_context=parser_context)

        data = json.loads(result.data["data"])

        # Flatten the result.files MultiValueDict.
        # If the "files" is not flatten, the serializer would receive the data like this:
        # <MultiValueDict: {'file': [<InMemoryUploadedFile: filename.jpg (image/jpeg)>]}>
        # The serializer wouldn't find the file because the value is an array, not a single File
        files = {}
        for key in result.files.keys():
            files[key] = result.files.get(key)

        return parsers.DataAndFiles(data, files)


class FileMixin:
    def create(self, request, *args, **kwargs):
        """Use the Class.serializer_class after the creation for returning the saved data.
        Instead of a different serializer used in 'create' action."""
        if not self.serializer_class:
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        read_serializer = self.serializer_class(serializer.instance, context=serializer.context)

        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """Use the Class.serializer_class after update for returning the saved data.
        Instead of a different serializer used in 'update' action."""
        if not self.serializer_class:
            return super().create(request, *args, **kwargs)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        read_serializer = self.serializer_class(serializer.instance, context=serializer.context)

        return Response(read_serializer.data)

    @action(methods=['get'], detail=True)
    def download(self, request, pk=None):
        obj = self.get_object()

        filename = '/'.join([settings.MEDIA_ROOT, obj.file.name])
        base_filename = os.path.basename(obj.file.name)

        with open(filename, 'rb') as fp:
            # TODO: detect file MIME type
            response = HttpResponse(File(fp), content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(base_filename)

            return response
