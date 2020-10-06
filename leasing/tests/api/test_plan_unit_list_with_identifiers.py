import pytest
from django.urls import reverse

from leasing.enums import PlanUnitStatus


@pytest.mark.django_db
def test_plan_unit_list_with_identifiers(
    django_db_setup, admin_client, plan_unit_factory, lease_test_data
):
    # Add plan unit to contract
    plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        in_contract=True,
        plan_unit_status=PlanUnitStatus.PRESENT,
    )

    # Add pending plan unit
    plan_unit_factory(
        identifier="PU2",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        in_contract=True,
        plan_unit_status=PlanUnitStatus.PENDING,
    )

    # Add not contracted plan unit
    plan_unit_factory(
        identifier="PU3",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        in_contract=False,
    )

    url = reverse("planunitlistwithidentifiers-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    results = response.data["results"]
    assert len(results) == 2
