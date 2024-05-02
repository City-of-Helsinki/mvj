import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_custom_detailed_plan_list_with_identifiers(
    django_db_setup, admin_client, custom_detailed_plan_factory, lease_test_data
):
    # Add plan unit to contract
    custom_detailed_plan_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        intended_use_id=1,
        rent_build_permission=500,
    )

    url = reverse("v1:customdetailedplanlistwithidentifiers-list")

    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    results = response.data["results"]
    assert len(results) == 1
