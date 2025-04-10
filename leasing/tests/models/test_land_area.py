from datetime import datetime

import pytest
from django.utils.timezone import make_aware

from leasing.models import LeaseArea, LeaseAreaAddress


@pytest.mark.django_db
def test_plan_unit_cannot_create_another_master_plan_unit(
    lease_test_data, plan_unit_factory
):
    master_plan_unit = plan_unit_factory(
        area=100,
        lease_area=lease_test_data["lease_area"],
        identifier="1234",
        is_master=True,
    )

    another_master_plan_unit = master_plan_unit
    another_master_plan_unit.pk = None

    with pytest.raises(Exception):
        another_master_plan_unit.save()


@pytest.mark.django_db
def test_lease_area_ordering(
    lease_area_factory,
):
    """
    The expected default ordering for LeaseArea is:
    - primary sort by archived_at, ascending, nulls first
    - secondary sort by id, ascending

    Unarchived areas must be returned before archived areas, to avoid
    picking an archived area where only one area can be shown.

    This helps maintain a shared ordering in all places of usage.
    """
    area6 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=1, day=2))
    )
    area5 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=1, day=1))
    )
    area1 = lease_area_factory(archived_at=None)
    area10 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=4, day=4))
    )
    area7 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=2, day=2))
    )
    area2 = lease_area_factory(archived_at=None)
    area3 = lease_area_factory(archived_at=None)
    area8 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=2, day=2))
    )
    area4 = lease_area_factory(archived_at=None)
    area9 = lease_area_factory(
        archived_at=make_aware(datetime(year=2024, month=3, day=3))
    )

    areas = list(LeaseArea.objects.all())
    expected_ordering = [
        area1,
        area2,
        area3,
        area4,
        area5,
        area6,
        area7,
        area8,
        area9,
        area10,
    ]
    assert areas == expected_ordering


@pytest.mark.django_db
def test_lease_area_address_ordering(
    lease_area_factory,
    lease_area_address_factory,
):
    """
    The expected default ordering for LeaseAreaAddress is:
    - primary sort by is_primary, True first
    - secondary sort by id, ascending

    Primary addresses must be returned before nonprimary addresses, to avoid
    picking a nonprimary address where only one address can be shown.

    This helps maintain a shared ordering in all places of usage.
    """
    area = lease_area_factory()
    address3 = lease_area_address_factory(is_primary=False, lease_area=area)
    address1 = lease_area_address_factory(is_primary=True, lease_area=area)
    address4 = lease_area_address_factory(is_primary=False, lease_area=area)
    address5 = lease_area_address_factory(is_primary=False, lease_area=area)
    address6 = lease_area_address_factory(is_primary=False, lease_area=area)
    address2 = lease_area_address_factory(is_primary=True, lease_area=area)
    address7 = lease_area_address_factory(is_primary=False, lease_area=area)

    addresses = list(LeaseAreaAddress.objects.all())
    expected_ordering = [
        address1,
        address2,
        address3,
        address4,
        address5,
        address6,
        address7,
    ]
    assert addresses == expected_ordering
