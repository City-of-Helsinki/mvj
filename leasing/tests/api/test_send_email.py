import json
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from leasing.enums import EmailLogType, PollutedLandRentConditionState
from leasing.models import EmailLog
from leasing.viewsets.email import send_constructability_reminder_email
from utils.email import EmailMessageInput


@pytest.mark.django_db
def test_send_email(django_db_setup, client, lease_test_data, user_factory):
    """Email sending works via the send-email API, and details are saved to email log."""
    user = user_factory(username="test_user", email="test_user@example.com")
    user.set_password("test_password")
    user.save()

    user2 = user_factory(username="test_user2", email="test_user2@example.com")
    user3 = user_factory(
        username="test_user3"
    )  # Users without email should not receive emails

    permission_names = ["view_lease"]
    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    lease = lease_test_data["lease"]
    email_body = "Test email text"

    data = {
        "type": EmailLogType.CONSTRUCTABILITY,
        "lease": lease.id,
        "recipients": [user2.id, user3.id],
        "text": email_body,
    }

    client.login(username="test_user", password="test_password")
    url = reverse("v1:send-email")

    with patch(
        "leasing.viewsets.email.send_email",
        return_value=MagicMock(status_code=200),
    ) as mock_send_email:
        response = client.post(
            url,
            data=json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

        # Email has been sent successfully
        assert mock_send_email.call_count == 1, "Email should be sent"
        assert response.status_code == 200, "%s %s" % (
            response.status_code,
            response.data,
        )

    # Details are logged to EmailLog
    email_log = EmailLog.objects.get(object_id=lease.id, user_id=user.id)
    assert email_log.content_object == lease
    assert email_log.type == EmailLogType.CONSTRUCTABILITY
    assert email_log.user == user
    assert email_log.text == email_body

    # Email was only sent to users with an email address (user2)
    assert email_log.recipients.count() == 1


@pytest.mark.django_db
def test_constructability_reminder_email_sent(
    admin_client, user_factory, lease_test_data
):
    """
    If email type is constructability, a reminder email should be scheduled,
    in addition to the initial email.
    """
    lease = lease_test_data["lease"]
    recipient = user_factory(email="recipient@example.com")
    lease = lease_test_data["lease"]
    data = {
        "type": EmailLogType.CONSTRUCTABILITY,
        "lease": lease.id,
        "recipients": [recipient.id],
        "text": "Test mail text",
    }
    admin_client.login(username="test_user", password="test_password")
    url = reverse("v1:send-email")

    # Emails are sent
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"sent": True}

    assert (
        len(mail.outbox) == 1
    ), "One email is sent immediately, and one is scheduled for later (not in outbox yet)"

    # Spy the view's different methods to compare their invocations
    with patch(
        "leasing.viewsets.email.send_email",
    ) as mock_initial_send, patch(
        "leasing.viewsets.email.SendEmailView._schedule_constructability_reminder_email"
    ) as mock_reminder_schedule:
        response = admin_client.post(
            url,
            data=json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )
        # Both the initial email and the reminder email should be attempted to be sent
        mock_initial_send.assert_called_once()
        mock_reminder_schedule.assert_called_once()

        # Reminder email is a follow-up to the initial email; it has similar contents
        initial_send_input = mock_initial_send.call_args_list[0][0][0]
        reminder_schedule_input = mock_reminder_schedule.call_args_list[0][0][0]

        assert initial_send_input["from_email"] == reminder_schedule_input["from_email"]
        assert initial_send_input["to"] == reminder_schedule_input["to"]
        assert initial_send_input["subject"] in reminder_schedule_input["subject"]
        assert initial_send_input["body"] == reminder_schedule_input["body"]


@pytest.mark.skip
def test_constructability_reminder_email_not_sent(
    admin_client, user_factory, lease_test_data
):
    """
    If email type is not constructability, a reminder email should not be scheduled.

    This test would be useful, but cannot be created at the moment, because
    there is only one EmailLogType defined in the enum, and the view and
    serializer don't allow allow inputs for any other type.

    --> Write this test when more EmailLogTypes are added.
    """
    pass


def test_constructability_reminder_email_conditions(
    admin_client, lease_test_data, lease_area_factory
):
    """
    Constructability reminder email is only sent if any active lease area has
    a polluted land rent condition state that is not READY.
    """
    lease = lease_test_data["lease"]

    email_input_dummy: EmailMessageInput = {
        "from_email": "test@example.com",
        "to": ["recipient@example.com"],
        "subject": "Test constructability email",
        "body": "Test email body",
        "attachments": [],
    }

    # Case 1: All active areas have READY state - no email should be sent
    lease.lease_areas.all().update(
        polluted_land_rent_condition_state=PollutedLandRentConditionState.READY,
        archived_at=None,
    )
    with patch("leasing.viewsets.email.send_email") as mock_send_email:
        send_constructability_reminder_email(email_input_dummy, lease.id)
        mock_send_email.assert_not_called()

    # Case 2: At least one active area has non-READY state - email should be sent
    lease.lease_areas.all().update(
        polluted_land_rent_condition_state=PollutedLandRentConditionState.READY,
        archived_at=None,
    )
    nonready_area = lease.lease_areas.first()
    nonready_area.polluted_land_rent_condition_state = (
        PollutedLandRentConditionState.ASKED
    )
    nonready_area.save()
    with patch("leasing.viewsets.email.send_email") as mock_send_email:
        send_constructability_reminder_email(email_input_dummy, lease.id)
        mock_send_email.assert_called_once_with(email_input_dummy)

    # Case 3: Archived areas are ignored, even if they have non-READY state
    lease.lease_areas.all().update(
        polluted_land_rent_condition_state=PollutedLandRentConditionState.READY,
        archived_at=None,
    )
    lease_area_factory(
        lease=lease,
        identifier="archived-area1",
        polluted_land_rent_condition_state=PollutedLandRentConditionState.ASKED,
        archived_at=timezone.now(),
    )
    lease_area_factory(
        lease=lease,
        identifier="archived-area2",
        polluted_land_rent_condition_state=None,
        archived_at=timezone.now(),
    )
    with patch("leasing.viewsets.email.send_email") as mock_send_email:
        send_constructability_reminder_email(email_input_dummy, lease.id)
        mock_send_email.assert_not_called()
