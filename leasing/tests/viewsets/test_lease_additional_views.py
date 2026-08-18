import datetime
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from leasing.enums import InvoiceState, TenantContactType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LEASES_FOR_CONTACT_URL = "v1:leases_for_contact-list"


def _url(contact_id):
    return reverse(LEASES_FOR_CONTACT_URL) + f"?contact={contact_id}"


# ---------------------------------------------------------------------------
# LeasesForContactViewSet – get_queryset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_leases_for_contact_missing_param(django_db_setup, admin_client):
    """Missing contact param should return 500."""
    response = admin_client.get(reverse(LEASES_FOR_CONTACT_URL))
    assert response.status_code == 500


@pytest.mark.django_db
def test_leases_for_contact_invalid_param(django_db_setup, admin_client):
    """Non-integer contact param should return 500."""
    response = admin_client.get(reverse(LEASES_FOR_CONTACT_URL) + "?contact=abc")
    assert response.status_code == 500


@pytest.mark.django_db
def test_leases_for_contact_returns_only_matching_lease(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
):
    """Only leases where the contact is a tenantcontact should be returned."""
    lease_a = lease_factory(type_id=1, municipality_id=1, district_id=1)
    lease_b = lease_factory(type_id=1, municipality_id=1, district_id=1)

    contact = contact_factory()
    other_contact = contact_factory()

    tenant_a = tenant_factory(lease=lease_a, share_numerator=1, share_denominator=1)
    tenant_b = tenant_factory(lease=lease_b, share_numerator=1, share_denominator=1)

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant_a,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant_b,
        contact=other_contact,
        start_date=datetime.date(2020, 1, 1),
    )

    lease_a.tenants.set([tenant_a])
    lease_b.tenants.set([tenant_b])

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert lease_a.id in ids
    assert lease_b.id not in ids


@pytest.mark.django_db
def test_leases_for_contact_excludes_soft_deleted_tenants(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
):
    """Leases reachable only through a soft-deleted tenant should not be returned."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    # Soft-delete the tenant
    tenant.delete()

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.django_db
def test_leases_for_contact_no_duplicates(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
):
    """A contact linked to the same lease via two tenantcontacts should appear once."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)

    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    tenant_contact_factory(
        type=TenantContactType.CONTACT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_leases_for_contact_has_overdue_invoices_true(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    invoice_factory,
):
    """has_overdue_invoices should be True for a lease with an open past-due invoice."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    invoice_factory(
        lease=lease,
        state=InvoiceState.OPEN,
        due_date=datetime.date(2020, 1, 1),  # past due
        total_amount=Decimal("100.00"),
        billed_amount=Decimal("100.00"),
        outstanding_amount=Decimal("100.00"),
    )

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["results"][0]["has_overdue_invoices"] is True


@pytest.mark.django_db
def test_leases_for_contact_has_overdue_invoices_false_when_no_invoice(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
):
    """has_overdue_invoices should be False when there are no invoices."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["results"][0]["has_overdue_invoices"] is False


@pytest.mark.django_db
def test_leases_for_contact_has_overdue_invoices_false_when_zero_outstanding(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    invoice_factory,
):
    """has_overdue_invoices should be False when outstanding_amount is zero."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    invoice_factory(
        lease=lease,
        state=InvoiceState.OPEN,
        due_date=datetime.date(2020, 1, 1),
        total_amount=Decimal("100.00"),
        billed_amount=Decimal("100.00"),
        outstanding_amount=Decimal("0.00"),
    )

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["results"][0]["has_overdue_invoices"] is False


@pytest.mark.django_db
def test_leases_for_contact_has_overdue_invoices_false_when_future_due_date(
    django_db_setup,
    admin_client,
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    invoice_factory,
):
    """has_overdue_invoices should be False when the invoice is not yet due."""
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1)
    contact = contact_factory()
    tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        contact=contact,
        start_date=datetime.date(2020, 1, 1),
    )
    lease.tenants.set([tenant])

    invoice_factory(
        lease=lease,
        state=InvoiceState.OPEN,
        due_date=datetime.date(9999, 12, 31),
        total_amount=Decimal("100.00"),
        billed_amount=Decimal("100.00"),
        outstanding_amount=Decimal("100.00"),
    )

    response = admin_client.get(_url(contact.id))
    assert response.status_code == 200
    assert response.data["results"][0]["has_overdue_invoices"] is False
