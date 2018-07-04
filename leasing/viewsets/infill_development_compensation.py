import os

from django.conf import settings
from django.core.files import File
from django.http import HttpResponse
from rest_framework.decorators import action

from leasing.models import InfillDevelopmentCompensation, InfillDevelopmentCompensationAttachment
from leasing.serializers.infill_development_compensation import (
    InfillDevelopmentCompensationAttachmentCreateUpdateSerializer, InfillDevelopmentCompensationAttachmentSerializer,
    InfillDevelopmentCompensationCreateUpdateSerializer, InfillDevelopmentCompensationSerializer)

from .utils import AtomicTransactionModelViewSet, AuditLogMixin, MultiPartJsonParser


class InfillDevelopmentCompensationViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    queryset = InfillDevelopmentCompensation.objects.all()
    serializer_class = InfillDevelopmentCompensationSerializer

    def get_queryset(self):
        queryset = InfillDevelopmentCompensation.objects.select_related('user').prefetch_related(
            'infill_development_compensation_leases',
            'infill_development_compensation_leases__lease',
            'infill_development_compensation_leases__lease__identifier',
            'infill_development_compensation_leases__lease__type',
            'infill_development_compensation_leases__lease__municipality',
            'infill_development_compensation_leases__lease__district',
            'infill_development_compensation_leases__lease__identifier__type',
            'infill_development_compensation_leases__lease__identifier__municipality',
            'infill_development_compensation_leases__lease__identifier__district',
        )

        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return InfillDevelopmentCompensationCreateUpdateSerializer

        return InfillDevelopmentCompensationSerializer


class InfillDevelopmentCompensationAttachmentViewSet(AuditLogMixin, AtomicTransactionModelViewSet):
    queryset = InfillDevelopmentCompensationAttachment.objects.all()
    serializer_class = InfillDevelopmentCompensationAttachmentSerializer
    parser_classes = (MultiPartJsonParser, )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update', 'metadata'):
            return InfillDevelopmentCompensationAttachmentCreateUpdateSerializer

        return InfillDevelopmentCompensationAttachmentSerializer

    @action(methods=['get'], detail=True)
    def download(self, request, pk=None):
        attachment = self.get_object()

        filename = '/'.join([settings.MEDIA_ROOT, attachment.file.name])
        base_filename = os.path.basename(attachment.file.name)

        with open(filename, 'rb') as fp:
            response = HttpResponse(File(fp), content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(base_filename)

            return response
