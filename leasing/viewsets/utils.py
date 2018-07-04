import json

from auditlog.middleware import AuditlogMiddleware
from django.db import transaction
from rest_framework import parsers, viewsets


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
