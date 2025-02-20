import datetime

import pytest

from leasing.enums import TenantContactType
from leasing.models import Contact
from leasing.models.tenant import TenantContact
from leasing.models.types import TenantShares
from leasing.report.lease.contact_rents import ContactRentsReport


@pytest.fixture
def tenant_shares_data(tenant_contact_factory, tenant_factory, lease_factory):
    lease = lease_factory()
    tenant = tenant_factory(lease=lease, share_numerator=11, share_denominator=73)
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    tenantcontact_type_billing = tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant,
        start_date=start_date,
        end_date=end_date,
    )
    tenantcontact_type_tenant = tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant,
        start_date=start_date,
        end_date=end_date,
    )
    tenantcontact_type_contact = tenant_contact_factory(
        type=TenantContactType.CONTACT,
        start_date=start_date,
        end_date=end_date,
    )
    tenant_shares = TenantShares()
    contact_billing: Contact = tenantcontact_type_billing.contact
    tenant_shares[contact_billing] = {tenant: [(start_date, end_date)]}

    return {
        "lease": lease,
        "tenant": tenant,
        "tenantcontact_type_tenant": tenantcontact_type_tenant,
        "tenantcontact_type_contact": tenantcontact_type_contact,
        "tenant_shares": tenant_shares,
        "date_range": (start_date, end_date),
    }


@pytest.mark.django_db
def test_get_contacts_tenant_from_tenant_shares(tenant_shares_data):
    """Validates that the function returns the Tenant for a Contact which is of type `TENANT`,
    from `tenant_shares` that only have Contacts of type `BILLING`, but both Contacts sharing
    the same Tenant."""
    tenant_shares = tenant_shares_data["tenant_shares"]
    lease = tenant_shares_data["lease"]
    tenant = tenant_shares_data["tenant"]
    tenantcontact_type_tenant: TenantContact = tenant_shares_data[
        "tenantcontact_type_tenant"
    ]
    tenantcontact_type_contact: TenantContact = tenant_shares_data[
        "tenantcontact_type_contact"
    ]
    date_range = tenant_shares_data["date_range"]
    report = ContactRentsReport()

    result_tenant = report._get_tenant_from_tenant_shares(
        tenantcontact_type_tenant.contact, lease, tenant_shares, date_range
    )
    assert result_tenant == tenant

    result_tenant = report._get_tenant_from_tenant_shares(
        tenantcontact_type_contact.contact, lease, tenant_shares, date_range
    )
    # The TenantContact is expected to have different Tenant
    assert result_tenant != tenantcontact_type_contact.tenant
    assert result_tenant is None
