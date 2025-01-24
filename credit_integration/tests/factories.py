import factory
from factory import Faker, fuzzy

from conftest import ServiceUnitFactory
from credit_integration.enums import CreditDecisionStatus
from credit_integration.models import CreditDecision, CreditDecisionReason
from leasing.enums import ContactType
from leasing.models import Contact, ServiceUnit
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    username = Faker("email")
    email = Faker("email")


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    type = fuzzy.FuzzyChoice(ContactType)
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    name = Faker("name")
    # Gets around the issue that service_unit with id 1 exists due to migration
    # `leasing/migrations/0063_initialize_service_units.py`
    # when running test with migrations. This works also with `--no-migrations`` flag.
    service_unit = factory.LazyFunction(
        lambda: ServiceUnit.objects.first() or ServiceUnitFactory()
    )


class BusinessContactFactory(ContactFactory):
    class Meta:
        model = Contact

    type = ContactType.BUSINESS


class CreditDecisionReasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CreditDecisionReason

    reason_code = factory.Sequence(lambda n: "{}".format(n).zfill(3))
    reason = Faker("paragraph", nb_sentences=1)


class CreditDecisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CreditDecision

    status = fuzzy.FuzzyChoice(CreditDecisionStatus)
    claimant = factory.SubFactory(UserFactory)

    @factory.post_generation
    def reasons(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for reason in extracted:
                self.reasons.add(reason)


class BusinessCreditDecisionFactory(CreditDecisionFactory):
    class Meta:
        model = CreditDecision

    customer = factory.SubFactory(BusinessContactFactory)
    status = fuzzy.FuzzyChoice(CreditDecisionStatus)
    official_name = Faker("company")
    address = Faker("address")
    phone_number = Faker("phone_number")
    business_entity = fuzzy.FuzzyChoice(["Oy"])
    operation_start_date = Faker("date")
    industry_code = Faker("pystr_format", string_format="###", letters="0123456789")
