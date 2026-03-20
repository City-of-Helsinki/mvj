from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import ValidationError

from leasing.serializers.debt_collection import (
    CollectionCourtDecisionCreateUpdateSerializer,
)


@pytest.mark.django_db
def test_validate_court_decision_superuser_allowed(
    lease_with_generated_service_unit_factory,
    user_factory,
):
    """
    CollectionCourtDecisionCreateUpdateSerializer should allow a superuser to add a court decision for any lease.
    """
    superuser = user_factory(is_superuser=True)
    request = MagicMock()
    request.user = superuser
    serializer = CollectionCourtDecisionCreateUpdateSerializer(
        context={"request": request}
    )

    data = {"lease": lease_with_generated_service_unit_factory()}
    assert serializer.validate(data) == data


@pytest.mark.django_db
@pytest.mark.parametrize("user_has_correct_service_unit", [False, True])
def test_validate_court_decision_service_unit_access(
    lease_test_data,
    service_unit_factory,
    user_factory,
    user_has_correct_service_unit,
):
    """
    CollectionCourtDecisionCreateUpdateSerializer should allow a normal user to add a court decision
    only when the user belongs to the same service unit as the invoice's lease.
    """

    lease = lease_test_data["lease"]
    other_service_unit = service_unit_factory()
    normal_user = user_factory(
        service_units=[
            lease.service_unit if user_has_correct_service_unit else other_service_unit
        ]
    )
    request = MagicMock()
    request.user = normal_user
    serializer = CollectionCourtDecisionCreateUpdateSerializer(
        context={"request": request}
    )
    data = {"lease": lease}

    if user_has_correct_service_unit:
        assert serializer.validate(data) == data
    else:
        with pytest.raises(ValidationError):
            serializer.validate(data)
