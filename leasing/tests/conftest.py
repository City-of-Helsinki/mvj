import datetime
import unittest
from decimal import Decimal
from pathlib import Path

import factory
import pytest
from django.core.management import call_command
from django.utils import timezone
from django.utils.crypto import get_random_string
from pytest_factoryboy import register

from leasing.enums import (
    ContactType, IndexType, InvoiceState, InvoiceType, LeaseAreaType, LocationType, RentAdjustmentType, RentCycle,
    RentType, TenantContactType)
from leasing.models import (
    Condition, Contact, ContractRent, Decision, District, FixedInitialYearRent, Invoice, Lease, LeaseArea,
    LeaseBasisOfRent, LeaseType, Municipality, NoticePeriod, RelatedLease, Rent, RentAdjustment, Tenant, TenantContact,
    UiData)
from leasing.models.invoice import InvoiceNote, InvoicePayment, InvoiceRow, InvoiceSet, ReceivableType
from leasing.models.tenant import TenantRentShare
from users.models import User


@pytest.fixture()
def assert_count_equal():
    def do_test(a, b):
        tc = unittest.TestCase()
        tc.assertCountEqual(a, b)

    return do_test


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Loads all the database fixtures in the leasing/fixtures folder"""
    fixture_path = Path(__file__).parents[1] / 'fixtures'
    fixture_filenames = [path for path in fixture_path.glob('*') if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command('loaddata', *fixture_filenames)


@register
class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact


@register
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


@register
class LeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Lease


@register
class RelatedLeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = RelatedLease


@register
class TenantFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tenant


@register
class TenantContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenantContact


@register
class TenantRentShareFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenantRentShare


@register
class LeaseTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = LeaseType


@register
class MunicipalityFactory(factory.DjangoModelFactory):
    class Meta:
        model = Municipality


@register
class DistrictFactory(factory.DjangoModelFactory):
    class Meta:
        model = District


@register
class NoticePeriodFactory(factory.DjangoModelFactory):
    class Meta:
        model = NoticePeriod


@register
class RentFactory(factory.DjangoModelFactory):
    type = RentType.INDEX
    cycle = RentCycle.JANUARY_TO_DECEMBER
    index_type = IndexType.TYPE_7

    class Meta:
        model = Rent


@register
class ContractRentFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContractRent


@register
class RentAdjustmentFactory(factory.DjangoModelFactory):
    type = RentAdjustmentType.DISCOUNT

    class Meta:
        model = RentAdjustment


@register
class FixedInitialYearRentFactory(factory.DjangoModelFactory):
    class Meta:
        model = FixedInitialYearRent


@register
class LeaseAreaFactory(factory.DjangoModelFactory):
    type = LeaseAreaType.REAL_PROPERTY
    location = LocationType.SURFACE

    class Meta:
        model = LeaseArea


@register
class InvoiceFactory(factory.DjangoModelFactory):
    state = InvoiceState.OPEN
    due_date = timezone.now().date()
    type = InvoiceType.CHARGE

    class Meta:
        model = Invoice


@register
class InvoiceNoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = InvoiceNote


@register
class InvoiceRowFactory(factory.DjangoModelFactory):
    class Meta:
        model = InvoiceRow


@register
class InvoiceSetFactory(factory.DjangoModelFactory):
    class Meta:
        model = InvoiceSet


@register
class InvoicePaymentFactory(factory.DjangoModelFactory):
    class Meta:
        model = InvoicePayment


@register
class DecisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Decision


@register
class ConditionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Condition


@register
class UiDataFactory(factory.DjangoModelFactory):
    class Meta:
        model = UiData


@register
class LeaseBasisOfRentFactory(factory.DjangoModelFactory):
    class Meta:
        model = LeaseBasisOfRent


@pytest.fixture
def lease_test_data(lease_factory, contact_factory, tenant_factory, tenant_contact_factory, lease_area_factory):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
    )

    contacts = [contact_factory(first_name="Lessor First name", last_name="Lessor Last name", is_lessor=True,
                                type=ContactType.PERSON)]
    for i in range(3):
        contacts.append(contact_factory(first_name="First name " + str(i), last_name="Last name " + str(i),
                                        type=ContactType.PERSON))

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    tenants = [tenant1, tenant2]

    tenantcontacts = [
        tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contacts[1],
                               start_date=timezone.now().date()),
        tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant2, contact=contacts[2],
                               start_date=timezone.now().date()),
        tenant_contact_factory(type=TenantContactType.CONTACT, tenant=tenant2, contact=contacts[3],
                               start_date=timezone.now().date()),
    ]

    lease.tenants.set(tenants)

    lease_area_factory(lease=lease, identifier=get_random_string(), area=1000, section_area=1000)

    return {
        'lease': lease,
        'tenants': tenants,
        'tenantcontacts': tenantcontacts,
    }


@pytest.fixture
def invoices_test_data(lease_factory, contact_factory, tenant_factory, invoice_factory, invoice_row_factory):
    receivable_type = ReceivableType.objects.get(pk=1)

    lease = lease_factory(type_id=1, municipality_id=1, district_id=5, notice_period_id=1)

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)
    contact2 = contact_factory(first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON)

    billing_period_start_date = datetime.date(year=2018, month=1, day=1)
    billing_period_end_date = datetime.date(year=2018, month=12, day=31)

    # Same recipients and tenants
    invoice1 = invoice_factory(
        lease=lease,
        total_amount=Decimal(500),
        billed_amount=Decimal(500),
        outstanding_amount=Decimal(500),
        due_date=datetime.date(year=2018, month=10, day=15),
        recipient=contact1,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date
    )

    invoice_row_factory(
        invoice=invoice1,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(500),
    )

    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal(100),
        billed_amount=Decimal(100),
        outstanding_amount=Decimal(100),
        due_date=datetime.date(year=2018, month=10, day=1),
        recipient=contact1,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    return {
        'lease': lease,
        'tenant1': tenant1,
        'tenant2': tenant2,
        'contact1': contact1,
        'contact2': contact2,
        'invoice1': invoice1,
        'invoice2': invoice2,
    }
