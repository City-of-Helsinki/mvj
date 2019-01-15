import datetime
import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Condition


@pytest.mark.django_db
def test_patch_decision_condition_can_change_some_fields(django_db_setup, client, lease_test_data, user_factory,
                                                         condition_factory, decision_factory):
    user = user_factory(username='test_user')
    user.set_password('test_password')
    user.save()

    permission_names = [
        'change_decision',
        'change_decision_conditions',
        'view_condition_type',
        'change_condition_supervision_date',
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    lease = lease_test_data['lease']

    decision = decision_factory(lease=lease)
    condition = condition_factory(
        decision=decision,
        type_id=1,
        description="Test condition",
        supervision_date=datetime.date(year=2018, month=1, day=1)
    )

    data = {
        "conditions": [
            {
                "id": condition.id,
                "type": 2,
                "supervision_date": datetime.date(year=2018, month=1, day=2),
            },
        ],
    }

    client.login(username='test_user', password='test_password')
    url = reverse('decision-detail', kwargs={'pk': decision.id})
    response = client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    condition = Condition.objects.get(pk=condition.id)

    assert condition.type_id == 1
    assert condition.supervision_date == datetime.date(year=2018, month=1, day=2)
