import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["A1128-1", " A1128-1", "A1128-1 ", " A1128-1 "])
@pytest.mark.parametrize("param_name", ["search", "identifier"])
def test_search_finds_one_lease_by_full_identifier(
    django_db_setup, admin_client, lease_factory, value, param_name
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=29, notice_period_id=1
    )
    lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1)

    response = admin_client.get(reverse("lease-list"), data={param_name: value})

    assert response.status_code == 200, "%s %s" % (
        response.status_code,
        response.data,
    )

    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == lease.id


@pytest.mark.django_db
@pytest.mark.parametrize("param_name", ["search", "identifier"])
def test_search_finds_one_lease_by_full_identifier_where_type_has_two_letters(
    django_db_setup, admin_client, lease_factory, param_name
):
    lease = lease_factory(
        type_id=33, municipality_id=1, district_id=1, notice_period_id=1
    )
    lease_factory(type_id=33, municipality_id=1, district_id=2, notice_period_id=1)

    response = admin_client.get(reverse("lease-list"), data={param_name: "MA100-1"})

    assert response.status_code == 200, "%s %s" % (
        response.status_code,
        response.data,
    )

    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == lease.id
