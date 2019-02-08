import json

import pytest
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.enums import EmailLogType
from leasing.models import EmailLog


@pytest.mark.django_db
def test_send_email(django_db_setup, client, lease_test_data, user_factory):
    user = user_factory(username='test_user', email="test_user@example.com")
    user.set_password('test_password')
    user.save()

    user2 = user_factory(username='test_user2', email="test_user2@example.com")
    # User without email address. Shouldn't try to send email to them.
    user3 = user_factory(username='test_user3')

    permission_names = [
        'view_lease',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    lease = lease_test_data['lease']

    data = {
        "type": "constructability",
        "lease": lease.id,
        "recipients": [user2.id, user3.id],
        "text": "Test mail text"
    }

    client.login(username='test_user', password='test_password')
    url = reverse('send-email')
    response = client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)
    assert len(mail.outbox) == 1
    assert EmailLog.objects.count() == 1

    email_log = EmailLog.objects.first()

    assert email_log.content_object == lease
    assert email_log.type == EmailLogType.CONSTRUCTABILITY
    assert email_log.user == user
    assert email_log.text == "Test mail text"
    assert email_log.recipients.count() == 1
