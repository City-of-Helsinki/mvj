import datetime

import pytest
from django.urls import reverse

from leasing.enums import ContactType, TenantContactType


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

    response = admin_client.get(reverse("v1:lease-list"), data={param_name: value})

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

    response = admin_client.get(reverse("v1:lease-list"), data={param_name: "MA100-1"})

    assert response.status_code == 200, "%s %s" % (
        response.status_code,
        response.data,
    )

    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == lease.id


@pytest.mark.parametrize(
    "tenantcontact_type, tenant_activity, expected_result_count",
    [
        ("", "all", 1),
        (TenantContactType.TENANT.value, "active", 1),
        (TenantContactType.BILLING.value, "all", 0),
        ("", "past", 0),
    ],
)
@pytest.mark.django_db
def test_business_id_affects_tenantcontact_type_and_tenant_activity_filters(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_contact_factory,
    contact_factory,
    tenantcontact_type,
    tenant_activity,
    expected_result_count,
):
    business_id = "1234567-8"
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
    )
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
    )
    contact = contact_factory(
        first_name="First name",
        last_name="Last name",
        business_id=business_id,
        type=ContactType.BUSINESS,
    )
    start_date = datetime.date(2000, 1, 1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=start_date,
    )

    response = admin_client.get(
        reverse("v1:lease-list"),
        data={
            "business_id": business_id,
            "tenantcontact_type": tenantcontact_type,
            "tenant_activity": tenant_activity,
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == expected_result_count
