from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_q.tasks import schedule
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.enums import EmailLogType
from leasing.metadata import FieldsMetadata
from leasing.models.email import EmailLog
from leasing.permissions import PerMethodPermission
from leasing.serializers.email import SendEmailSerializer
from utils.email import EmailMessageInput, send_email


class SendEmailView(APIView):
    permission_classes = (PerMethodPermission,)
    metadata_class = FieldsMetadata
    perms_map = {"POST": ["leasing.view_lease"]}

    def get_view_name(self):
        return _("Send email")

    def get_view_description(self, html=False):
        return _("Send email")

    def post(self, request, format=None):
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_type = serializer.validated_data["type"]
        email_body = serializer.validated_data["text"]
        lease = serializer.validated_data["lease"]

        email_log = EmailLog.objects.create(
            type=email_type,
            user=request.user,
            text=email_body,
            content_object=lease,
        )

        if request.user.email:
            from_email = request.user.email
        else:
            from_email = settings.MVJ_EMAIL_FROM

        for recipient in serializer.validated_data["recipients"]:
            if not recipient.email:
                continue

            email_input: EmailMessageInput = {
                "from_email": from_email,
                "to": [recipient.email],
                "subject": _("MVJ lease {} {}").format(
                    lease.identifier,
                    email_type,
                ),
                "body": email_body,
                "attachments": [],
            }
            send_email(email_input)
            email_log.recipients.add(recipient)

            if email_type == EmailLogType.CONSTRUCTABILITY:
                self._schedule_constructability_reminder_email(email_input)

        result = {"sent": True}

        return Response(result, status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        if self.metadata_class is None:
            return self.http_method_not_allowed(request, *args, **kwargs)

        data = self.metadata_class().determine_metadata(
            request, self, serializer=SendEmailSerializer()
        )

        return Response(data, status=status.HTTP_200_OK)

    def _schedule_constructability_reminder_email(
        self, email_input: EmailMessageInput
    ) -> None:
        """Constructability emails come with a reminder email."""
        reminder_subject = _("Reminder: {}").format(email_input["subject"])
        email_input["subject"] = reminder_subject
        reminder_time = timezone.now() + relativedelta(days=14)
        schedule(
            "utils.email.send_email",
            email_input,
            next_run=reminder_time,
            schedule_type="O",  # Once
        )
