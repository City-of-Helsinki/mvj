import json
from datetime import date, datetime

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.models import Lease, PlanUnit


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value, expected_value, expected_code",
    [
        ("", False, 500),
        (None, False, 500),
        (-1, False, 500),
        (0, False, 500),
        (1, False, 500),
        (5, False, 500),
        (True, True, 200),
        (False, False, 200),
    ],
)
def test_set_invoicing_state(
    django_db_setup, admin_client, lease_test_data, value, expected_value, expected_code
):
    lease = lease_test_data["lease"]
    lease.is_rent_info_complete = True
    lease.save()

    assert lease.is_invoicing_enabled is False

    data = {"invoicing_enabled": value}

    url = reverse("lease-set-invoicing-state") + "?lease={}".format(lease.id)

    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == expected_code, "%s %s" % (
        response.status_code,
        response.data,
    )

    lease = Lease.objects.get(pk=lease.id)

    assert lease.is_invoicing_enabled is expected_value


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value, expected_value, expected_code",
    [
        ("", False, 500),
        (None, False, 500),
        (-1, False, 500),
        (0, False, 500),
        (1, False, 500),
        (5, False, 500),
        (True, True, 200),
        (False, False, 200),
    ],
)
def test_set_rent_info_completion_state(
    django_db_setup, admin_client, lease_test_data, value, expected_value, expected_code
):
    lease = lease_test_data["lease"]

    assert lease.is_rent_info_complete is False

    data = {"rent_info_complete": value}

    url = reverse("lease-set-rent-info-completion-state") + "?lease={}".format(lease.id)

    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == expected_code, "%s %s" % (
        response.status_code,
        response.data,
    )

    lease = Lease.objects.get(pk=lease.id)

    assert lease.is_rent_info_complete is expected_value


@pytest.mark.django_db
def test_lease_details_contains_future_tenants(
    django_db_setup, admin_client, lease_test_data
):
    """ Related user stories:
    - As a user, I want to send an invoice for the tenant which are not yet actives
    """

    url = reverse("lease-detail", kwargs={"pk": lease_test_data["lease"].id})

    response = admin_client.get(url, content_type="application/json",)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data,)

    found = False
    for tenant in response.data["tenants"]:
        for tenantcontact in tenant["tenantcontact_set"]:
            if (
                datetime.strptime(tenantcontact["start_date"], "%Y-%m-%d").date()
                > date.today()
            ):
                found = True
                break
            if found:
                break

    assert found is True


@pytest.mark.django_db
def test_copy_areas_to_contract(
    django_db_setup, admin_client, plan_unit_factory, lease_test_data
):
    lease = lease_test_data["lease"]
    lease_area = lease_test_data["lease_area"]

    plan_unit_factory(
        identifier="PU1", area=1000, lease_area=lease_area, in_contract=False,
    )

    assert PlanUnit.objects.filter(lease_area=lease_area, in_contract=True).count() == 0

    url = reverse("lease-copy-areas-to-contract") + "?lease={}".format(lease.id)
    response = admin_client.post(url, content_type="application/json",)

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert PlanUnit.objects.filter(lease_area=lease_area, in_contract=True).count() == 1
