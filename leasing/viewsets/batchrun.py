from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from batchrun import models
from leasing.serializers.batchrun import (
    JobRunLogEntrySerializer,
    JobRunSerializer,
    JobSerializer,
    ScheduledJobSerializer,
)


class JobRunLogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.JobRunLogEntry.objects.all()
    serializer_class = JobRunLogEntrySerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["run", "kind"]
    ordering = ("-time",)


class JobRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.JobRun.objects.all()
    serializer_class = JobRunSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["exit_code"]
    ordering = ("-started_at",)


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Job.objects.all()
    serializer_class = JobSerializer


class ScheduledJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.ScheduledJob.objects.all()
    serializer_class = ScheduledJobSerializer
