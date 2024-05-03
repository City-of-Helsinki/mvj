import json

import pytest
from django.contrib.auth.models import Permission
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.enums import ContactType
from leasing.models import Contact


@pytest.mark.django_db
@pytest.mark.parametrize("change_service_unit", [None, False, True])
def test_patch_contact_should_validate_service_unit(
    client,
    user_factory,
    service_unit_factory,
    contact_factory,
    change_service_unit,
):
    service_unit = service_unit_factory(name="First service unit")
    contact = contact_factory(
        type=ContactType.BUSINESS, name="Test contact", service_unit=service_unit
    )
    service_unit2 = service_unit_factory(name="Second service unit")

    user = user_factory(username="test_user")
    user.service_units.add(service_unit)
    user.service_units.add(service_unit2)

    permission_names = [
        "change_contact",
        "view_contact_id",
        "change_contact_type",
        "change_contact_name",
        "change_contact_service_unit",
    ]

    for permission_name in permission_names:
        user.user_permissions.add(Permission.objects.get(codename=permission_name))

    client.force_login(user)

    data = {
        "name": "New name",
    }

    if change_service_unit is not None:
        data["service_unit"] = (
            service_unit2.id if change_service_unit else service_unit.id
        )

    url = reverse("v1:contact-detail", kwargs={"pk": contact.id})

    response = client.patch(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    if change_service_unit:
        assert response.status_code == 400, "%s %s" % (
            response.status_code,
            response.data,
        )
    else:
        assert response.status_code == 200, "%s %s" % (
            response.status_code,
            response.data,
        )

        contact = Contact.objects.get(pk=response.data["id"])
        assert contact.name == "New name"
        assert contact.service_unit == service_unit
