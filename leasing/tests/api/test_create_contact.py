import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.enums import ContactType
from leasing.models import Contact


@pytest.mark.django_db
@pytest.mark.parametrize("with_request_service_unit", [False, True])
@pytest.mark.parametrize("with_user_service_unit", [False, True])
def test_create_contact_should_validate_service_unit(
    client,
    user_factory,
    service_unit_factory,
    with_request_service_unit,
    with_user_service_unit,
):
    service_unit = service_unit_factory()

    user = user_factory(username="test_user")
    if with_user_service_unit:
        user.service_units.add(service_unit)

    permission_names = [
        "add_contact",
        "view_contact_id",
        "change_contact_type",
        "change_contact_name",
        "change_contact_service_unit",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.force_login(user)

    data = {
        "type": ContactType.BUSINESS.value,
        "name": "Test contact",
    }

    if with_request_service_unit:
        data["service_unit"] = {"id": service_unit.id}

    url = reverse("contact-list")

    response = client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    if not with_request_service_unit:
        assert response.status_code == 400, "%s %s" % (
            response.status_code,
            response.data,
        )
    else:
        if with_user_service_unit:
            assert response.status_code == 201, "%s %s" % (
                response.status_code,
                response.data,
            )
            contact = Contact.objects.get(pk=response.data["id"])
            assert contact.service_unit == service_unit
        else:
            assert response.status_code == 400, "%s %s" % (
                response.status_code,
                response.data,
            )
