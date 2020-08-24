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
    ContactType,
    IndexType,
    InvoiceState,
    InvoiceType,
    LandUseContractType,
    LeaseAreaType,
    LocationType,
    RentAdjustmentType,
    RentCycle,
    RentType,
    TenantContactType,
)
from leasing.models import (
    Condition,
    Contact,
    Contract,
    ContractRent,
    Decision,
    DecisionMaker,
    District,
    FixedInitialYearRent,
    Invoice,
    Lease,
    LeaseArea,
    LeaseBasisOfRent,
    LeaseType,
    Municipality,
    NoticePeriod,
    RelatedLease,
    Rent,
    RentAdjustment,
    Tenant,
    TenantContact,
    UiData,
)
from leasing.models.invoice import (
    InvoiceNote,
    InvoicePayment,
    InvoiceRow,
    InvoiceSet,
    ReceivableType,
)
from leasing.models.land_area import LeaseAreaAddress
from leasing.models.land_use_agreement import (
    LandUseAgreement,
    LandUseAgreementAddress,
    LandUseAgreementDefinition,
    LandUseAgreementIdentifier,
    LandUseAgreementInvoice,
    LandUseAgreementStatus,
    LandUseAgreementType,
)
from leasing.models.tenant import TenantRentShare
from users.models import User


@pytest.fixture()
def assert_count_equal():
    def do_test(a, b):
        tc = unittest.TestCase()
        tc.assertCountEqual(a, b)

    return do_test


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Loads all the database fixtures in the leasing/fixtures folder"""
    fixture_path = Path(__file__).parents[1] / "fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)


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
class LeaseAreaAddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = LeaseAreaAddress


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


@register
class LandUseAgreementFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreement


@register
class LandUseAgreementTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreementType


@register
class LandUseAgreementStatusFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreementStatus


@register
class LandUseAgreementDefinitionFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreementDefinition


@register
class LandUseAgreementIdentifierFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreementIdentifier


@register
class LandUseAgreementAddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = LandUseAgreementAddress


@register
class LandUseAgreementInvoiceFactory(factory.DjangoModelFactory):
    due_date = timezone.now().date()

    class Meta:
        model = LandUseAgreementInvoice


@register
class ContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = Contract


@register
class DecisionMakerFactory(factory.DjangoModelFactory):
    class Meta:
        model = DecisionMaker


@pytest.fixture
def lease_test_data(
    lease_factory,
    contact_factory,
    tenant_factory,
    tenant_contact_factory,
    lease_area_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=1, notice_period_id=1
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

    lease_area_factory(
        lease=lease, identifier=get_random_string(), area=1000, section_area=1000
    )

    return {"lease": lease, "tenants": tenants, "tenantcontacts": tenantcontacts}


@pytest.fixture
def invoices_test_data(
    lease_factory, contact_factory, tenant_factory, invoice_factory, invoice_row_factory
):
    receivable_type = ReceivableType.objects.get(pk=1)

    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    contact1 = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )

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
        billing_period_end_date=billing_period_end_date,
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
        billing_period_end_date=billing_period_end_date,
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
        "lease": lease,
        "tenant1": tenant1,
        "tenant2": tenant2,
        "contact1": contact1,
        "contact2": contact2,
        "invoice1": invoice1,
        "invoice2": invoice2,
    }


@pytest.fixture
def lease_data_dict_with_contacts(contact_factory):
    test_contacts = [
        contact_factory(
            first_name="First name",
            last_name="Last name",
            is_lessor=True,
            type=ContactType.PERSON,
        )
    ]
    for i in range(3):
        test_contacts.append(
            contact_factory(
                first_name="First name " + str(i),
                last_name="Last name " + str(i),
                type=ContactType.PERSON,
            )
        )

    data = {
        "state": "lease",
        "classification": "public",
        "intended_use_note": "Intended use note...",
        "transferable": True,
        "regulated": False,
        "notice_note": "Notice note...",
        "type": 1,
        "municipality": 1,
        "district": 31,
        "intended_use": 1,
        "supportive_housing": 5,
        "statistical_use": 1,
        "financing": 1,
        "management": 1,
        "regulation": 1,
        "hitas": 1,
        "notice_period": 1,
        "lessor": test_contacts[0].id,
        "tenants": [
            {
                "share_numerator": 1,
                "share_denominator": 2,
                "reference": "123",
                "tenantcontact_set": [
                    {
                        "type": "tenant",
                        "contact": test_contacts[1].id,
                        "start_date": timezone.now().date(),
                    },
                    {
                        "type": "billing",
                        "contact": test_contacts[3].id,
                        "start_date": timezone.now().date(),
                    },
                ],
            },
            {
                "share_numerator": 1,
                "share_denominator": 2,
                "reference": "345",
                "tenantcontact_set": [
                    {
                        "type": "tenant",
                        "contact": test_contacts[2].id,
                        "start_date": timezone.now().date(),
                    }
                ],
            },
        ],
        "lease_areas": [
            {
                "identifier": "12345",
                "area": 100,
                "section_area": 100,
                "address": "Testaddress 1",
                "postal_code": "00100",
                "city": "Helsinki",
                "type": "real_property",
                "location": "surface",
                "plots": [
                    {
                        "identifier": "plot-1",
                        "area": 100,
                        "section_area": 100,
                        "address": "Test plotaddress 1",
                        "postal_code": "00100",
                        "city": "Helsinki",
                        "type": "real_property",
                        "registration_date": None,
                        "in_contract": True,
                    }
                ],
            }
        ],
    }
    return data


@pytest.fixture
def land_use_agreement_test_data(
    land_use_agreement_factory,
    land_use_agreement_identifier_factory,
    land_use_agreement_type_factory,
    land_use_agreement_status_factory,
    land_use_agreement_definition_factory,
    land_use_agreement_address_factory,
    user_factory,
    decision_maker_factory,
    contract_factory,
):
    identifier = land_use_agreement_identifier_factory(
        sequence=1, district_id=1, municipality_id=1, type_id=1
    )
    land_use_agreement_type = land_use_agreement_type_factory(name="Test type")
    land_use_agreement_status = land_use_agreement_status_factory(name="Test status")
    land_use_agreement_definition = land_use_agreement_definition_factory(
        name="Test definition"
    )
    preparer = user_factory(username="test_preparer")
    plan_acceptor = decision_maker_factory(name="test_plan_acceptor")
    land_use_agreement = land_use_agreement_factory(
        type_id=land_use_agreement_type.id,
        preparer=preparer,
        land_use_contract_type=LandUseContractType.LAND_USE_AGREEMENT,
        identifier=identifier,
        status_id=land_use_agreement_status.id,
        definition_id=land_use_agreement_definition.id,
        estimated_completion_year=2021,
        estimated_introduction_year=2020,
        project_area="test project area",
        plan_reference_number="TESTREFNUM",
        plan_number="TESTPLANNUM",
        plan_lawfulness_date=datetime.date(year=2021, month=1, day=1),
        plan_acceptor=plan_acceptor,
    )
    land_use_agreement_address_factory(
        land_use_agreement=land_use_agreement, address="Testikatu 1"
    )
    contract_factory(
        land_use_agreement=land_use_agreement, type_id=1, contract_number="A123"
    )

    return land_use_agreement
