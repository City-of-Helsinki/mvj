from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from batchrun import models


class CommandSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Command
        fields = "__all__"


class TimeZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Timezone
        fields = "__all__"


class JobSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    command = CommandSerializer()

    class Meta:
        model = models.Job
        fields = "__all__"


class ScheduledJobSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    job = JobSerializer()
    timezone = TimeZoneSerializer()
    next_run = SerializerMethodField()

    class Meta:
        model = models.ScheduledJob
        fields = "__all__"

    def get_next_run(self, obj):
        queue_item = (
            models.JobRunQueueItem.objects.filter(scheduled_job=obj, assigned_at=None)
            .order_by("run_at")
            .first()
        )

        if queue_item:
            return queue_item.run_at


class JobRunSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    job = JobSerializer()

    class Meta:
        model = models.JobRun
        fields = "__all__"


class JobRunLogEntrySerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    enumfield_options = {"ints_as_names": True}

    class Meta:
        model = models.JobRunLogEntry
        fields = "__all__"
