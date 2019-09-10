from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from leasing.metadata import FieldsMetadata
from leasing.models.email import EmailLog
from leasing.permissions import PerMethodPermission
from leasing.serializers.email import SendEmailSerializer


class SendEmailView(APIView):
    permission_classes = (PerMethodPermission,)
    metadata_class = FieldsMetadata
    perms_map = {
        'POST': ['leasing.view_lease'],
    }

    def get_view_name(self):
        return _("Send email")

    def get_view_description(self, html=False):
        return _("Send email")

    def post(self, request, format=None):
        serializer = SendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_log = EmailLog.objects.create(
            type=serializer.validated_data['type'],
            user=request.user,
            text=serializer.validated_data['text'],
            content_object=serializer.validated_data['lease'],
        )

        if request.user.email:
            from_email = request.user.email
        else:
            from_email = settings.MVJ_EMAIL_FROM

        for recipient in serializer.validated_data['recipients']:
            if not recipient.email:
                continue

            send_mail(
                _('MVJ lease {} {}').format(serializer.validated_data['lease'].identifier,
                                            serializer.validated_data['type']),
                serializer.validated_data['text'],
                from_email,
                [recipient.email],
                fail_silently=False,
            )

            email_log.recipients.add(recipient)

        result = {
            "sent": True,
        }

        return Response(result, status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        if self.metadata_class is None:
            return self.http_method_not_allowed(request, *args, **kwargs)

        data = self.metadata_class().determine_metadata(request, self, serializer=SendEmailSerializer())

        return Response(data, status=status.HTTP_200_OK)
