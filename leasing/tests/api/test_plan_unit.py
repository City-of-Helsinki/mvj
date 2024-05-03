import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_plan_unit_detail(
    django_db_setup, admin_client, plan_unit_factory, lease_test_data
):
    # Add plan unit for lease area
    plan_unit_factory(
        identifier="PU1",
        area=1000,
        lease_area=lease_test_data["lease_area"],
        is_master=True,
    )

    url = reverse("v1:planunitlistwithidentifiers-list")

    response = admin_client.get(url, content_type="application/json")
    plan_unit_id = response.data["results"][0]["id"]

    url = reverse("v1:planunit-detail", kwargs={"pk": plan_unit_id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
