from auditlog.models import LogEntry
from rest_framework import serializers

from users.serializers import UserSerializer


class LogEntrySerializer(serializers.ModelSerializer):
    actor = UserSerializer()

    class Meta:
        model = LogEntry
        exclude = (
            "remote_addr",
            "remote_port",
            "object_pk",
            "additional_data",
            "serialized_data",
            "cid",
            "changes_text",
            "actor_email",
        )

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result["action"] = LogEntry.Action.choices[instance.action][1]
        result["changes"] = instance.changes_dict
        result["content_type"] = instance.content_type.model
        result["content_type_name"] = instance.content_type.name

        if (
            len(result["changes"]) == 1
            and "deleted" in result["changes"]
            and result["changes"]["deleted"][0] == "None"
        ):
            result["action"] = "delete"

        for field_name in list(result["changes"].keys()):
            view_permission_name = "{}.view_{}_{}".format(
                instance.content_type.app_label,
                instance.content_type.model,
                field_name,
            )
            change_permission_name = "{}.change_{}_{}".format(
                instance.content_type.app_label,
                instance.content_type.model,
                field_name,
            )
            if not self.context["request"].user.has_perm(
                view_permission_name
            ) and not self.context["request"].user.has_perm(change_permission_name):
                del result["changes"][field_name]

        return result
