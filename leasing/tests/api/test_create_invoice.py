import datetime
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Callable

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType, InvoiceRowType, InvoiceState, TenantContactType
from leasing.models.invoice import Invoice, InvoiceRow

if TYPE_CHECKING:
    from leasing.models.contact import Contact
    from leasing.models.lease import Lease
    from leasing.models.receivable_type import ReceivableType
    from leasing.models.service_unit import ServiceUnit
    from leasing.models.tenant import Tenant, TenantContact, TenantRentShare
    from users.models import User


@pytest.mark.django_db
def test_create_invoice(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    data = {
        "lease": lease.id,
        "recipient": contact1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(10)
    assert invoice.state == InvoiceState.OPEN
    assert invoice.service_unit_id == 1


@pytest.mark.django_db
def test_create_invoice_before_tenant_contract_is_activated(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date.today() + datetime.timedelta(days=30),
    )

    data = {
        "lease": lease.id,
        "recipient": contact1.id,
        "due_date": datetime.date.today() + datetime.timedelta(days=2),
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(10)
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_create_zero_sum_invoice_state_is_paid(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    data = {
        "lease": lease.id,
        "recipient": contact1.id,
        "due_date": "2019-01-01",
        "rows": [
            {"amount": Decimal(10), "receivable_type": 1},
            {"amount": Decimal(-10), "receivable_type": 1},
        ],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_create_invoice_for_tenant(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    data = {
        "lease": lease.id,
        "tenant": tenant1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(10)
    assert invoice.recipient == contact1
    assert invoice.rows.first().tenant == tenant1


@pytest.mark.django_db
def test_create_invoice_for_tenant_with_billing_contact(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    data = {
        "lease": lease.id,
        "tenant": tenant1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(10)
    assert invoice.recipient == contact2
    assert invoice.rows.first().tenant == tenant1


@pytest.mark.django_db
def test_create_invoice_tenant_not_in_lease(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )
    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )
    tenant2 = tenant_factory(lease=lease2, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant2, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant2,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    data = {
        "lease": lease.id,
        "tenant": tenant2.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_interest_invoice_fail(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    data = {
        "lease": lease.id,
        "recipient": contact1.id,
        "due_date": "2030-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 2}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_invoice_checks_service_unit(
    django_db_setup,
    client,
    service_unit_factory,
    user_factory,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    service_unit2 = service_unit_factory()
    permission_names = [
        "add_invoice",
        "add_invoicerow",
        "view_invoice_id",
        "change_invoice_recipient",
        "change_invoice_due_date",
        "change_invoice_rows",
        "change_invoicerow_receivable_type",
        "change_invoicerow_amount",
    ]
    user = user_factory(
        username="test_user",
        service_units=[service_unit2],
        permissions=permission_names,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    client.force_login(user)

    data = {
        "lease": lease.id,
        "recipient": contact1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_invoice_cannot_add_row_with_receivable_type_from_another_service_unit(
    django_db_setup,
    client,
    service_unit_factory,
    user_factory,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
    receivable_type_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    service_unit = lease.service_unit

    permission_names = [
        "add_invoice",
        "add_invoicerow",
        "view_invoice_id",
        "change_invoice_recipient",
        "change_invoice_due_date",
        "change_invoice_rows",
        "change_invoicerow_receivable_type",
        "change_invoicerow_amount",
    ]
    user = user_factory(
        username="test_user",
        service_units=[service_unit],
        permissions=permission_names,
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
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

    client.force_login(user)

    service_unit2 = service_unit_factory()
    receivable_type = receivable_type_factory(
        name="Test receivable type",
        service_unit=service_unit2,
    )

    data = {
        "lease": lease.id,
        "service_unit": service_unit.id,
        "recipient": contact1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(10), "receivable_type": receivable_type.id}],
    }

    url = reverse("v1:invoice-list")
    response = client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 400, "%s %s" % (response.status_code, response.data)


@pytest.mark.django_db
def test_create_invoice_row_types(
    admin_client: Client,
    lease_factory: Callable[..., "Lease"],
    tenant_factory: Callable[..., "Tenant"],
    tenant_rent_share_factory: Callable[..., "TenantRentShare"],
    contact_factory: Callable[..., "Contact"],
    tenant_contact_factory: Callable[..., "TenantContact"],
):
    """InvoiceRows with positive or zero amounts are CHARGE, negative amounts are CREDIT"""
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    data = {
        "lease": lease.id,
        "recipient": contact.id,
        "due_date": "2026-01-01",
        "rows": [
            {
                "amount": Decimal(100),
                "receivable_type": 1,
            },  # Type not given, deduce the CHARGE type from amount
            {
                "amount": Decimal(-100),
                "receivable_type": 1,
            },  # Type not given, deduce the CREDIT type from amount
            {
                "amount": Decimal(-0.01).quantize(
                    Decimal(".01")
                ),  # quantize to avoid float precision issues
                "receivable_type": 1,
                "type": InvoiceRowType.ROUNDING.value,  # use the given type
            },
            {
                "amount": Decimal(0),
                "receivable_type": 1,
                "type": InvoiceRowType.CREDIT.value,  # use the given type, even if amount is not negative
            },
            {
                "amount": Decimal(-100),
                "receivable_type": 1,
                "type": None,  # Type is None, deduce the CREDIT type from amount
            },
        ],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )
    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data["id"])
    created_rows = InvoiceRow.objects.filter(invoice=invoice).order_by("id")

    assert len(created_rows) == 5

    # Type not given, deduced from positive amount
    assert created_rows[0].type == InvoiceRowType.CHARGE
    assert created_rows[0].amount == data["rows"][0]["amount"]

    # Type not given, deduced from negative amount
    assert created_rows[1].type == InvoiceRowType.CREDIT
    assert created_rows[1].amount == data["rows"][1]["amount"]

    # Use the given type
    assert created_rows[2].type == InvoiceRowType.ROUNDING
    assert created_rows[2].amount == data["rows"][2]["amount"]

    # Use the given type, even if amount is not negative
    assert created_rows[3].type == InvoiceRowType.CREDIT
    assert created_rows[3].amount == data["rows"][3]["amount"]

    # Type was given as None, deduced from negative amount
    assert created_rows[4].type == InvoiceRowType.CREDIT
    assert created_rows[4].amount == data["rows"][4]["amount"]
