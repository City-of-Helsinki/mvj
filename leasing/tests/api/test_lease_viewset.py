import json
from datetime import datetime
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import MultiPolygon
from django.core.serializers.json import DjangoJSONEncoder
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from leasing.enums import LocationType
from leasing.models import Lease


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
@pytest.mark.parametrize("user_has_correct_service_unit", [False, True])
def test_set_invoicing_state_checks_service_unit(
    django_db_setup,
    client,
    lease_factory,
    user_factory,
    service_unit_factory,
    user_has_correct_service_unit,
):
    """
    LeaseSetInvoicingStateView should deny the request when the user does not
    belong to the same service unit as the lease.
    """

    lease = lease_factory()
    lease.start_date = timezone.now()
    lease.rent_info_completed_at = timezone.now()
    lease.save()
    other_service_unit = service_unit_factory()
    user = user_factory(
        username="test_user",
        service_units=[
            lease.service_unit if user_has_correct_service_unit else other_service_unit
        ],
        permissions=["change_lease_invoicing_enabled_at"],
    )
    client.force_login(user)

    data = {"invoicing_enabled": True}
    url = reverse("v1:lease-set-invoicing-state") + "?lease={}".format(lease.id)

    response = client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    if user_has_correct_service_unit:
        assert response.status_code == 200, "%s %s" % (
            response.status_code,
            response.data,
        )
        lease.refresh_from_db()
        assert lease.invoicing_enabled_at is not None
    else:
        assert response.status_code == 403, "%s %s" % (
            response.status_code,
            response.data,
        )
        lease.refresh_from_db()
        assert lease.invoicing_enabled_at is None


@pytest.mark.django_db
def test_lease_id_by_identifier_returns_an_id(
    django_db_setup, admin_client, lease_factory
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    identifier = str(lease.identifier)
    response = admin_client.get(
        reverse("v1:lease-id-by-identifier"),
        data={"identifier": identifier},
    )

    assert response.status_code == 200
    assert response.data == {"id": lease.id}


@pytest.mark.django_db
def test_lease_identifier_by_id_returns_identifier(
    django_db_setup, admin_client, lease_factory
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )

    response = admin_client.get(
        reverse("v1:lease-identifier-by-id"), data={"id": lease.id}
    )

    assert response.status_code == 200
    assert response.data == str(lease.identifier)


@pytest.mark.django_db
def test_related_areas_returns_areas_from_related_lease_graph(
    admin_client, lease_factory, lease_area_factory, related_lease_factory
):
    root = lease_factory()
    direct_relation = lease_factory()
    transitive_relation = lease_factory()
    unrelated = lease_factory()
    related_lease_factory(from_lease=root, to_lease=direct_relation)
    related_lease_factory(from_lease=direct_relation, to_lease=transitive_relation)

    direct_area = lease_area_factory(
        lease=direct_relation,
        geometry=MultiPolygon(),
    )
    transitive_area = lease_area_factory(
        lease=transitive_relation,
        geometry=MultiPolygon(),
    )
    lease_area_factory(
        lease=unrelated,
        geometry=MultiPolygon(),
    )

    response = admin_client.get(reverse("v1:lease-related-areas", args=[root.pk]))

    assert response.status_code == 200
    assert response.data["type"] == "FeatureCollection"
    assert {feature["properties"]["id"] for feature in response.data["features"]} == {
        direct_area.id,
        transitive_area.id,
    }


@pytest.mark.django_db
def test_related_areas_excludes_archived_and_underground_areas(
    admin_client, lease_factory, lease_area_factory, related_lease_factory
):
    root = lease_factory()
    related = lease_factory()
    related_lease_factory(from_lease=root, to_lease=related)

    visible_area = lease_area_factory(
        lease=related,
        geometry=MultiPolygon(),
    )
    lease_area_factory(
        lease=related,
        geometry=MultiPolygon(),
        archived_at=timezone.now(),
    )
    lease_area_factory(
        lease=related,
        geometry=MultiPolygon(),
        location=LocationType.UNDERGROUND,
    )

    response = admin_client.get(reverse("v1:lease-related-areas", args=[root.pk]))

    assert response.status_code == 200
    assert {feature["properties"]["id"] for feature in response.data["features"]} == {
        visible_area.id
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "required_permission",
    ("lease_related_leases", "lease_lease_areas", "leasearea_geometry"),
)
def test_related_areas_requires_all_permissions(
    admin_client, admin_user, lease_factory, required_permission
):
    lease = lease_factory()
    denied_permissions = {
        f"leasing.view_{required_permission}",
        f"leasing.change_{required_permission}",
    }

    def has_permission(user, permission, obj=None):
        return permission not in denied_permissions

    with patch.object(admin_user.__class__, "has_perm", has_permission):
        response = admin_client.get(reverse("v1:lease-related-areas", args=[lease.pk]))

    assert response.status_code == 403
