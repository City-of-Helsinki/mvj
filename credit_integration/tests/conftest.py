import faker.config
from pytest import fixture
from pytest_factoryboy import register
from rest_framework.test import APIClient

from credit_integration.tests.factories import (
    BusinessContactFactory,
    BusinessCreditDecisionFactory,
    ContactFactory,
    CreditDecisionFactory,
    CreditDecisionReasonFactory,
)

faker.config.DEFAULT_LOCALE = "fi_FI"

register(ContactFactory)
register(BusinessContactFactory)
register(CreditDecisionReasonFactory)
register(CreditDecisionFactory)
register(BusinessCreditDecisionFactory)


@fixture
def api_client():
    return APIClient()
