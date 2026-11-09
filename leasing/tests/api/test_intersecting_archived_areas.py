import datetime
from unittest.mock import patch

import pytest
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.urls import reverse
from django.utils import timezone

from leasing.enums import LocationType


def geometry(left=0, bottom=0, right=1, top=1):
    return MultiPolygon(Polygon.from_bbox((left, bottom, right, top)), srid=4326)


def url(lease):
    return reverse("v1:lease-intersecting-archived-areas", args=[lease.pk])


@pytest.mark.django_db
def test_intersections(admin_client, lease_factory, lease_area_factory):
    today = timezone.localdate()
    current = lease_factory(end_date=today)
    lease_area_factory(lease=current, geometry=geometry())
    lease_area_factory(lease=current, geometry=geometry(5, 5, 6, 6))
    lease_area_factory(
        lease=current, geometry=geometry(10, 10, 11, 11), archived_at=timezone.now()
    )
    expired = lease_factory(end_date=today - datetime.timedelta(days=1))
    expected = [
        lease_area_factory(lease=expired, geometry=geometry(1, 0, 2, 1)),
        lease_area_factory(lease=expired, geometry=geometry(1, 1, 2, 2)),
        lease_area_factory(lease=expired, geometry=geometry(0.5, 0.5, 1.5, 1.5)),
        lease_area_factory(lease=expired, geometry=geometry(5, 5, 6, 6)),
        lease_area_factory(
            lease=expired, geometry=geometry(), archived_at=timezone.now()
        ),
        lease_area_factory(lease=lease_factory(end_date=today), geometry=geometry()),
    ]
    lease_area_factory(lease=expired, geometry=geometry(20, 20, 21, 21))
    lease_area_factory(lease=expired, geometry=geometry(10, 10, 11, 11))
    lease_area_factory(lease=expired, geometry=None)
    lease_area_factory(
        lease=expired, geometry=geometry(), location=LocationType.UNDERGROUND
    )
    lease_area_factory(lease=lease_factory(end_date=None), geometry=geometry())
    lease_area_factory(
        lease=lease_factory(end_date=today + datetime.timedelta(days=1)),
        geometry=geometry(),
    )
    deleted = lease_area_factory(lease=expired, geometry=geometry())
    deleted.delete()
    deleted_lease = lease_factory(end_date=today)
    lease_area_factory(lease=deleted_lease, geometry=geometry())
    deleted_lease.delete()

    response = admin_client.get(url(current))

    assert response.status_code == 200
    assert response.data["type"] == "FeatureCollection"
    assert {feature["properties"]["id"] for feature in response.data["features"]} == {
        area.pk for area in expected
    }
    feature = response.data["features"][0]
    assert feature["geometry"]["type"] == "MultiPolygon"
    assert feature["properties"]["lease"]["identifier"] == str(expired.identifier)
    assert (
        feature["properties"]["lease"]["service_unit"]["id"] == expired.service_unit_id
    )
    assert (
        feature["properties"]["lease"]["service_unit"]["name"]
        == expired.service_unit.name
    )


@pytest.mark.django_db
def test_no_geometry(admin_client, lease_factory, lease_area_factory):
    current = lease_factory()
    lease_area_factory(lease=current, geometry=None)
    response = admin_client.get(url(current))
    assert response.status_code == 200
    assert response.data == {"type": "FeatureCollection", "features": []}


@pytest.mark.django_db
def test_geometry_permission_required(admin_client, admin_user, lease_factory):
    current = lease_factory()

    def has_permission(user, permission, obj=None):
        return permission not in (
            "leasing.view_leasearea_geometry",
            "leasing.change_leasearea_geometry",
        )

    with patch.object(admin_user.__class__, "has_perm", has_permission):
        response = admin_client.get(url(current))
    assert response.status_code == 403


@pytest.mark.django_db
def test_area_field_permissions(
    admin_client, admin_user, lease_factory, lease_area_factory
):
    current = lease_factory()
    lease_area_factory(lease=current, geometry=geometry())
    lease_area_factory(
        lease=lease_factory(end_date=timezone.localdate()), geometry=geometry()
    )

    def has_permission(user, permission, obj=None):
        return permission not in (
            "leasing.view_leasearea_identifier",
            "leasing.change_leasearea_identifier",
            "leasing.view_lease_service_unit",
            "leasing.change_lease_service_unit",
        )

    with patch.object(admin_user.__class__, "has_perm", has_permission):
        response = admin_client.get(url(current))
    assert response.status_code == 200
    assert len(response.data["features"]) == 1
    assert "identifier" not in response.data["features"][0]["properties"]
    assert "service_unit" not in response.data["features"][0]["properties"]["lease"]


@pytest.mark.django_db
def test_authentication_required(client, lease_factory):
    response = client.get(url(lease_factory()))
    assert response.status_code in (401, 403)
