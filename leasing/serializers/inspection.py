from rest_framework import serializers

from field_permissions.serializers import FieldPermissionsSerializerMixin
from leasing.serializers.utils import FileSerializerMixin
from users.serializers import UserSerializer

from ..models import Inspection, InspectionAttachment


class InspectionAttachmentSerializer(
    FileSerializerMixin, FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = UserSerializer()
    file = serializers.SerializerMethodField("get_file_url")
    filename = serializers.SerializerMethodField("get_file_filename")

    class Meta:
        model = InspectionAttachment
        fields = ("id", "file", "filename", "uploader", "uploaded_at", "inspection")
        download_url_name = "inspectionattachment-download"

    def override_permission_check_field_name(self, field_name):
        if field_name == "filename":
            return "file"

        return field_name


class InspectionAttachmentCreateUpdateSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    uploader = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = InspectionAttachment
        fields = ("id", "file", "uploader", "uploaded_at", "inspection")
        read_only_fields = ("uploaded_at",)


class InspectionSerializer(
    FieldPermissionsSerializerMixin, serializers.ModelSerializer
):
    id = serializers.IntegerField(required=False)
    attachments = InspectionAttachmentSerializer(
        many=True, read_only=True, allow_null=True
    )

    class Meta:
        model = Inspection
        fields = (
            "id",
            "inspector",
            "supervision_date",
            "supervised_date",
            "description",
            "attachments",
        )
