import json
from datetime import datetime
from unittest.mock import patch

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from leasing.models import Lease, PlanUnit


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value, expected_invoicing_enabled_at, expected_response_code",
    [
        ("", None, 500),
        (None, None, 500),
        (-1, None, 500),
        (0, None, 500),
        (1, None, 500),
        (5, None, 500),
        (True, timezone.now(), 200),
        (False, None, 200),
    ],
)
def test_set_invoicing_state_inputs(
    django_db_setup,
    admin_client,
    lease_test_data,
    value,
    expected_invoicing_enabled_at,
    expected_response_code,
):
    """Test how each input should affect the response codes and values."""
    lease: Lease = lease_test_data["lease"]
    lease.start_date = timezone.now()
    lease.rent_info_completed_at = expected_invoicing_enabled_at
    lease.save()

    assert lease.invoicing_enabled_at is None

    data = {"invoicing_enabled": value}

    url = reverse("v1:lease-set-invoicing-state") + "?lease={}".format(lease.id)

    with patch(
        "django.utils.timezone.now",
        # Return value is mostly not needed to mock, but can't use None for it so defaulting to something.
        return_value=expected_invoicing_enabled_at or timezone.now(),
    ):
        response = admin_client.post(
            url,
            data=json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    assert (
        response.status_code == expected_response_code
    ), f"{response.status_code}, {response.data}"

    lease = Lease.objects.get(pk=lease.id)

    if isinstance(expected_invoicing_enabled_at, datetime):
        assert lease.invoicing_enabled_at == expected_invoicing_enabled_at
    else:
        assert lease.invoicing_enabled_at is expected_invoicing_enabled_at


@override_settings(LANGUAGE_CODE="en")
def test_set_invoicing_state_without_lease_start_date(
    django_db_setup, admin_client, lease_test_data
):
    """Invoicing should not be enabled if lease start date is not set"""
    lease_input: Lease = lease_test_data["lease"]
    lease_input.start_date = None  # Omit lease start date to trigger validation error
    lease_input.rent_info_completed_at = timezone.now()
    lease_input.save()

    assert lease_input.invoicing_enabled_at is None

    data = {"invoicing_enabled": True}
    url = reverse("v1:lease-set-invoicing-state") + "?lease={}".format(lease_input.id)

    with patch("django.utils.timezone.now", return_value=timezone.now()):
        response = admin_client.post(
            url,
            data=json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    assert response.status_code == 400, f"{response.status_code}, {response.data}"
    assert "must have a start date" in str(response.data[0])

    lease_from_db = Lease.objects.get(pk=lease_input.id)
    assert lease_from_db.invoicing_enabled_at is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "value, expected_value, expected_code",
    [
        ("", None, 500),
        (None, None, 500),
        (-1, None, 500),
        (0, None, 500),
        (1, None, 500),
        (5, None, 500),
        (True, timezone.now(), 200),
        (False, None, 200),
    ],
)
def test_set_rent_info_completion_state(
    django_db_setup, admin_client, lease_test_data, value, expected_value, expected_code
):
    lease = lease_test_data["lease"]

    assert lease.rent_info_completed_at is None

    data = {"rent_info_complete": value}

    url = reverse("v1:lease-set-rent-info-completion-state") + "?lease={}".format(
        lease.id
    )

    with patch(
        "django.utils.timezone.now",
        # Return value is mostly not needed to mock, but can't use None for it so defaulting to something.
        return_value=expected_value or timezone.now(),
    ):
        response = admin_client.post(
            url,
            data=json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    assert (
        response.status_code == expected_code
    ), f"{response.status_code}, {response.data}"

    lease = Lease.objects.get(pk=lease.id)

    if isinstance(expected_value, datetime):
        assert lease.rent_info_completed_at == expected_value
    else:
        assert lease.rent_info_completed_at is expected_value


@pytest.mark.django_db
def test_lease_details_contains_future_tenants(
    django_db_setup, admin_client, lease_test_data
):
    """Related user stories:
    - As a user, I want to send an invoice for the tenant which are not yet actives
    """

    url = reverse("v1:lease-detail", kwargs={"pk": lease_test_data["lease"].id})

    response = admin_client.get(
        url,
        content_type="application/json",
    )

    assert response.status_code == 200, f"{response.status_code}, {response.data}"

    found = False
    for tenant in response.data["tenants"]:
        for tenantcontact in tenant["tenantcontact_set"]:
            if timezone.make_aware(
                datetime.strptime(tenantcontact["start_date"], "%Y-%m-%d")
            ) > timezone.make_aware(datetime(year=2019, month=2, day=28)):
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
        identifier="PU1",
        area=1000,
        lease_area=lease_area,
        in_contract=False,
        is_master=True,
    )

    assert PlanUnit.objects.filter(lease_area=lease_area, in_contract=True).count() == 0

    url = reverse("v1:lease-copy-areas-to-contract") + "?lease={}".format(lease.id)
    response = admin_client.post(
        url,
        content_type="application/json",
    )

    assert response.status_code == 200, f"{response.status_code}, {response.data}"
    assert PlanUnit.objects.filter(lease_area=lease_area, in_contract=True).count() == 1
