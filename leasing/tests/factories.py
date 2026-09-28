import factory
from django.utils import timezone

from leasing.enums import (
    ContactType,
    IndexType,
    InvoiceState,
    InvoiceType,
    LeaseAreaType,
    LocationType,
    RentAdjustmentType,
    RentCycle,
    RentType,
)
from leasing.models import (
    Area,
    AreaSource,
    CollectionLetter,
    Condition,
    Contract,
    ContractRent,
    Decision,
    DecisionMaker,
    DecisionType,
    District,
    FixedInitialYearRent,
    InfillDevelopmentCompensation,
    InfillDevelopmentCompensationLease,
    Inspection,
    IntendedUse,
    Invoice,
    InvoiceNote,
    InvoicePayment,
    InvoiceRow,
    InvoiceSet,
    Lease,
    LeaseArea,
    LeaseAreaAddress,
    LeaseBasisOfRent,
    LeaseType,
    Municipality,
    NoticePeriod,
    PlanUnit,
    PlanUnitIntendedUse,
    Plot,
    RelatedLease,
    Rent,
    RentAdjustment,
    RentDueDate,
    RentIntendedUse,
    UiData,
)
from leasing.models.contact import Contact
from leasing.models.contract import (
    Collateral,
    CollateralType,
    ContractChange,
    ContractType,
)
from leasing.models.decision import ConditionType
from leasing.models.land_area import CustomDetailedPlan
from leasing.models.map_layers import VipunenMapLayer
from leasing.models.receivable_type import ReceivableType
from leasing.models.rent import (
    Index,
    IndexPointFigureYearly,
    LeaseBasisOfRentManagementSubvention,
    LeaseBasisOfRentTemporarySubvention,
    ManagementSubventionFormOfManagement,
    OldDwellingsInHousingCompaniesPriceIndex,
)
from leasing.models.service_unit import ServiceUnit, ServiceUnitGroupMapping
from leasing.models.tenant import Tenant, TenantContact, TenantRentShare
from users.tests.factories import UserFactory


class ServiceUnitFactory(factory.django.DjangoModelFactory):
    id = factory.Sequence(lambda n: n + 100)

    class Meta:
        model = ServiceUnit


class ContactFactory(factory.django.DjangoModelFactory):
    type = ContactType.PERSON

    @factory.lazy_attribute
    def service_unit(self):
        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = Contact


class AreaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Area


class AreaSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AreaSource


class IndexFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Index


class PlotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Plot


class RelatedLeaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RelatedLease


class TenantRentShareFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TenantRentShare


class LeaseTypeFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "A%10d" % n)

    class Meta:
        model = LeaseType


class NoticePeriodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NoticePeriod


class RentFactory(factory.django.DjangoModelFactory):
    type = RentType.INDEX
    cycle = RentCycle.JANUARY_TO_DECEMBER
    index_type = IndexType.TYPE_7

    class Meta:
        model = Rent


class RentDueDateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RentDueDate


class OldDwellingsInHousingCompaniesPriceIndexFactory(
    factory.django.DjangoModelFactory
):
    class Meta:
        model = OldDwellingsInHousingCompaniesPriceIndex


class IndexPointFigureYearlyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IndexPointFigureYearly


class ContractRentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContractRent


class RentAdjustmentFactory(factory.django.DjangoModelFactory):
    type = RentAdjustmentType.DISCOUNT

    class Meta:
        model = RentAdjustment


class FixedInitialYearRentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FixedInitialYearRent


class InvoiceFactory(factory.django.DjangoModelFactory):
    state = InvoiceState.OPEN
    due_date = factory.LazyFunction(lambda: timezone.now().date())
    type = InvoiceType.CHARGE
    recipient = factory.SubFactory(ContactFactory)

    @factory.lazy_attribute
    def service_unit(self):
        if self.lease and self.lease.service_unit:
            return self.lease.service_unit
        return None

    class Meta:
        model = Invoice


class InvoiceNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvoiceNote


class InvoiceRowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvoiceRow


class InvoiceSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvoiceSet


class InvoicePaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InvoicePayment


class ConditionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConditionType


class ConditionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Condition


class UiDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UiData


class ManagementSubventionFormOfManagementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ManagementSubventionFormOfManagement


class LeaseBasisOfRentManagementSubventionFactory(factory.django.DjangoModelFactory):
    management = factory.SubFactory(ManagementSubventionFormOfManagementFactory)

    class Meta:
        model = LeaseBasisOfRentManagementSubvention


class LeaseBasisOfRentTemporarySubventionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeaseBasisOfRentTemporarySubvention


class ContractTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContractType


class ContractFactory(factory.django.DjangoModelFactory):
    type = factory.SubFactory(ContractTypeFactory)

    class Meta:
        model = Contract


class ContractChangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ContractChange


class DecisionMakerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DecisionMaker


class CollateralTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CollateralType


class CollateralFactory(factory.django.DjangoModelFactory):
    type = factory.SubFactory(CollateralTypeFactory)

    class Meta:
        model = Collateral


class ServiceUnitGroupMappingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceUnitGroupMapping


class IntendedUseFactory(factory.django.DjangoModelFactory):
    service_unit = factory.SubFactory(ServiceUnitFactory)

    class Meta:
        model = IntendedUse


class RentIntendedUseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RentIntendedUse


class ReceivableTypeFactory(factory.django.DjangoModelFactory):
    @factory.lazy_attribute
    def service_unit(self):
        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = ReceivableType


class LeaseBasisOfRentFactory(factory.django.DjangoModelFactory):
    intended_use = factory.SubFactory(RentIntendedUseFactory)

    class Meta:
        model = LeaseBasisOfRent


class DecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Decision


class DecisionTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DecisionType


class VipunenMapLayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VipunenMapLayer


class MunicipalityFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "1%1d" % n)

    class Meta:
        model = Municipality


class DistrictFactory(factory.django.DjangoModelFactory):
    identifier = factory.Sequence(lambda n: "10%1d" % n)
    municipality = factory.SubFactory(MunicipalityFactory)

    class Meta:
        model = District


class LeaseFactory(factory.django.DjangoModelFactory):
    type = factory.SubFactory(LeaseTypeFactory)
    municipality = factory.SubFactory(MunicipalityFactory)
    district = factory.SubFactory(DistrictFactory)

    @factory.lazy_attribute
    def service_unit(self):
        try:
            return ServiceUnit.objects.get(pk=1)
        except ServiceUnit.DoesNotExist:
            return ServiceUnitFactory()

    class Meta:
        model = Lease


class LeaseWithGeneratedServiceUnitFactory(factory.django.DjangoModelFactory):
    type = factory.SubFactory(LeaseTypeFactory)
    municipality = factory.SubFactory(MunicipalityFactory)
    district = factory.SubFactory(DistrictFactory)
    service_unit = factory.SubFactory(ServiceUnitFactory)

    class Meta:
        model = Lease


class LeaseAreaFactory(factory.django.DjangoModelFactory):
    type = LeaseAreaType.REAL_PROPERTY
    location = LocationType.SURFACE
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease = factory.SubFactory(LeaseFactory)

    class Meta:
        model = LeaseArea


class PlanUnitIntendedUseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanUnitIntendedUse


class PlanUnitFactory(factory.django.DjangoModelFactory):
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease_area = factory.SubFactory(LeaseAreaFactory)
    plan_unit_intended_use = factory.SubFactory(PlanUnitIntendedUseFactory)
    identifier = factory.Iterator(
        ["91-1-30-1", "91-1-30-2", "91-1-30-3", "91-1-30-4", "91-1-30-5"]
    )

    class Meta:
        model = PlanUnit


class CustomDetailedPlanFactory(factory.django.DjangoModelFactory):
    area = factory.Iterator([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
    lease_area = factory.SubFactory(LeaseAreaFactory)
    rent_build_permission = factory.Sequence(lambda n: n)
    intended_use = factory.SubFactory(PlanUnitIntendedUseFactory)

    class Meta:
        model = CustomDetailedPlan


class LeaseAreaAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LeaseAreaAddress


class TenantFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseFactory)
    share_numerator = 1
    share_denominator = 5

    class Meta:
        model = Tenant


class TenantContactFactory(factory.django.DjangoModelFactory):
    tenant = factory.SubFactory(TenantFactory)
    contact = factory.SubFactory(ContactFactory)

    class Meta:
        model = TenantContact


class CollectionLetterFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)
    uploader = factory.SubFactory(UserFactory)

    class Meta:
        model = CollectionLetter


class InfillDevelopmentCompensationFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = InfillDevelopmentCompensation


class InfillDevelopmentCompensationLeaseFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)
    infill_development_compensation = factory.SubFactory(
        InfillDevelopmentCompensationFactory
    )

    class Meta:
        model = InfillDevelopmentCompensationLease


class InspectionFactory(factory.django.DjangoModelFactory):
    lease = factory.SubFactory(LeaseWithGeneratedServiceUnitFactory)

    class Meta:
        model = Inspection
