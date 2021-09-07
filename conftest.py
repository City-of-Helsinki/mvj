import datetime

import factory
import pytest
from django.utils import timezone
from pytest_factoryboy import register

from leasing.enums import ContactType, LeaseAreaType, LocationType, TenantContactType
from leasing.models import Contact, Lease, LeaseArea, PlanUnit, Tenant, TenantContact
from leasing.models.land_area import LeaseAreaAddress
from plotsearch.models import (
    PlotSearch,
    PlotSearchStage,
    PlotSearchSubtype,
    PlotSearchTarget,
    PlotSearchType,
)
from users.models import User


@pytest.fixture
def plot_search_test_data(
    plot_search_factory,
    plot_search_type_factory,
    plot_search_subtype_factory,
    plot_search_stage_factory,
    user_factory,
):
    plot_search_type = plot_search_type_factory(name="Test type")
    plot_search_subtype = plot_search_subtype_factory(
        name="Test subtype", plot_search_type=plot_search_type
    )
    plot_search_stage = plot_search_stage_factory(name="Test stage")
    preparer = user_factory(username="test_preparer")

    begin_at = timezone.now().replace(microsecond=0)
    end_at = (timezone.now() + timezone.timedelta(days=7)).replace(microsecond=0)

    plot_search = plot_search_factory(
        name="PS1",
        subtype=plot_search_subtype,
        stage=plot_search_stage,
        preparer=preparer,
        begin_at=begin_at,
        end_at=end_at,
    )

    return plot_search


@register
class PlotSearchFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearch


@register
class PlotSearchTargetFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchTarget


@register
class PlotSearchTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchType


@register
class PlotSearchSubtypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchSubtype


@register
class PlotSearchStageFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlotSearchStage


@register
class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User


@register
class PlanUnitFactory(factory.DjangoModelFactory):
    class Meta:
        model = PlanUnit


@pytest.fixture
def lease_test_data(
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    lease_area_factory,
    lease_area_address_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=29, notice_period_id=1
    )

    contacts = [
        contact_factory(
            first_name="Lessor First name",
            last_name="Lessor Last name",
            is_lessor=True,
            type=ContactType.PERSON,
        )
    ]
    for i in range(4):
        contacts.append(
            contact_factory(
                first_name="First name " + str(i),
                last_name="Last name " + str(i),
                type=ContactType.PERSON,
            )
        )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    tenants = [tenant1, tenant2]

    tenantcontacts = [
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant1,
            contact=contacts[1],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[2],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.CONTACT,
            tenant=tenant2,
            contact=contacts[3],
            start_date=timezone.now().replace(year=2019).date(),
        ),
        tenant_contact_factory(
            type=TenantContactType.TENANT,
            tenant=tenant2,
            contact=contacts[4],
            start_date=timezone.now().date()
            + datetime.timedelta(days=30),  # Future tenant
        ),
    ]

    lease.tenants.set(tenants)
    lease_area = lease_area_factory(
        lease=lease, identifier="12345", area=1000, section_area=1000,
    )

    lease_area_address_factory(lease_area=lease_area, address="Test street 1")
    lease_area_address_factory(
        lease_area=lease_area, address="Primary street 1", is_primary=True
    )

    return {
        "lease": lease,
        "lease_area": lease_area,
        "tenants": tenants,
        "tenantcontacts": tenantcontacts,
    }


@register
class LeaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = Lease


@register
class ContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contact


@register
class TenantFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tenant


@register
class TenantContactFactory(factory.DjangoModelFactory):
    class Meta:
        model = TenantContact


@register
class LeaseAreaAddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = LeaseAreaAddress


@register
class LeaseAreaFactory(factory.DjangoModelFactory):
    type = LeaseAreaType.REAL_PROPERTY
    location = LocationType.SURFACE

    class Meta:
        model = LeaseArea
