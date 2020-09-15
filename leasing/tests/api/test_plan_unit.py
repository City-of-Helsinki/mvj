import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_plan_unit_detail(django_db_setup, admin_client, lease_test_data):
    url = reverse("planunitlistwithidentifiers-list")

    response = admin_client.get(url, content_type="application/json")
    plan_unit_id = response.data["results"][0]["id"]

    url = reverse("planunit-detail", kwargs={"pk": plan_unit_id})
    response = admin_client.get(url, content_type="application/json")
    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
