import unittest
from pathlib import Path

import factory
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone
from pytest_factoryboy import register

from leasing.enums import ContactType, TenantContactType
from leasing.models import Contact, District, Lease, LeaseType, Municipality, NoticePeriod, Tenant, TenantContact


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
class TenantFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tenant


@register
class TenantContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenantContact


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


@pytest.fixture
def lease_test_data(lease_factory, contact_factory, tenant_factory, tenant_contact_factory):
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

    return {
        'lease': lease,
        'tenants': tenants,
        'tenantcontacts': tenantcontacts,
    }
