import datetime

import pytest
from django.urls import reverse

from leasing.enums import (
    ContactType,
    DueDatesType,
    RentCycle,
    RentType,
    TenantContactType,
)


# 1.1 Vuokraukset, joissa ei ole laskutus käynnissä
def test_invoicing_not_enabled(
    django_db_setup, admin_client, lease_factory, tenant_factory, lease_test_data
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_test_data["lease"]
    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        is_invoicing_enabled=True,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_factory(
        lease=lease2, share_numerator=1, share_denominator=1, reference="testreference"
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("invoicing_not_enabled")) == 1
    assert (
        response.data[0].get("invoicing_not_enabled")[0].get("lease_id")
        == lease.get_identifier_string()
    )


# 1.2 Vuokraukset, joissa ei ole vuokratiedot kunnossa
@pytest.mark.django_db
def test_rent_info_not_complete(
    django_db_setup, admin_client, lease_factory, lease_test_data
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_test_data["lease"]
    lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        is_rent_info_complete=True,
        start_date=datetime.date(year=2017, month=1, day=1),
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("rent_info_not_complete")) == 1
    assert (
        response.data[0].get("rent_info_not_complete")[0].get("lease_id")
        == lease.get_identifier_string()
    )


# 1.3 Vuokraukset, joissa ei ole vuokratietoja
@pytest.mark.django_db
def test_no_rents(
    django_db_setup, admin_client, lease_factory, lease_test_data, rent_factory
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_test_data["lease"]
    rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )
    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("no_rents")) == 1
    assert (
        response.data[0].get("no_rents")[0].get("lease_id")
        == lease2.get_identifier_string()
    )


# 1.4 Vuokraukset, joissa ei ole eräpäivää (Vuokraukset, joissa vuokralaji on valittu, mutta ei ole eräpäivää)
@pytest.mark.django_db
def test_no_due_date(django_db_setup, admin_client, lease_test_data):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_test_data["lease"]

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("no_due_date")) == 1
    assert (
        response.data[0].get("no_due_date")[0].get("lease_id")
        == lease.get_identifier_string()
    )


# 1.5 Vuokraukset, joilla on kertakaikkinen vuokra mutta ei ole laskuja.
@pytest.mark.django_db
def test_one_time_rents_with_no_invoice(
    django_db_setup, admin_client, lease_test_data, rent_factory
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_test_data["lease"]
    rent_factory(
        lease=lease,
        type=RentType.ONE_TIME,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("one_time_rents_with_no_invoice")) == 1
    assert (
        response.data[0].get("one_time_rents_with_no_invoice")[0].get("lease_id")
        == lease.get_identifier_string()
    )


# 1.6 Vuokraukset, joissa on virheellinen hallintaosuus
@pytest.mark.django_db
def test_incorrect_management_shares(
    django_db_setup, admin_client, lease_factory, tenant_factory
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_factory(
        lease=lease, share_numerator=1, share_denominator=1, reference="testreference"
    )
    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_factory(
        lease=lease2, share_numerator=2, share_denominator=1, reference="testreference"
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("incorrect_management_shares")) == 1
    assert (
        response.data[0].get("incorrect_management_shares")[0].get("lease_id")
        == lease2.get_identifier_string()
    )


# 1.7 Vuokraukset, joissa on virheellinen laskutusosuus
@pytest.mark.django_db
def test_incorrect_rent_shares(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant1 = tenant_factory(
        lease=lease, share_numerator=1, share_denominator=1, reference="testreference"
    )
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )

    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant2 = tenant_factory(
        lease=lease2, share_numerator=1, share_denominator=1, reference="testreference"
    )
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=1, share_numerator=2, share_denominator=1
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("incorrect_rent_shares")) == 1
    assert (
        response.data[0].get("incorrect_rent_shares")[0].get("lease_id")
        == lease2.get_identifier_string()
    )


# 1.8 Vuokraukset, joissa ei ole voimassaolevaa vuokraajaa
def test_no_tenant_contact(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    contact_factory,
    tenant_contact_factory,
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant1 = tenant_factory(
        lease=lease, share_numerator=1, share_denominator=1, reference="testreference"
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant2 = tenant_factory(
        lease=lease2, share_numerator=2, share_denominator=1, reference="testreference"
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
        end_date=datetime.date(year=2000, month=2, day=1),
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("no_tenant_contact")) == 1
    assert (
        response.data[0].get("no_tenant_contact")[0].get("lease_id")
        == lease2.get_identifier_string()
    )


# 1.9 Vuokraukset, joissa ei ole vuokrakohdetta
def test_no_lease_area(
    django_db_setup, admin_client, lease_factory, tenant_factory, lease_test_data
):
    url = reverse("report-detail", kwargs={"report_type": "lease_lists"})
    data = {"start_date": "2019-01-01", "end_date": "2019-02-01"}
    lease_test_data["lease"]
    lease2 = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2017, month=1, day=1),
    )
    tenant_factory(
        lease=lease2, share_numerator=1, share_denominator=1, reference="testreference"
    )

    response = admin_client.get(url, data=data, content_type="application/json")

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)
    assert len(response.data) == 1
    assert len(response.data[0].get("no_lease_area")) == 1
    assert (
        response.data[0].get("no_lease_area")[0].get("lease_id")
        == lease2.get_identifier_string()
    )
