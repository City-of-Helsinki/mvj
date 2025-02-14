import datetime

import pytest
from django.utils import timezone

from leasing.report.lease.decision_conditions_report import DecisionConditionsReport


@pytest.fixture
def setup_data(
    db,
    lease_factory,
    condition_factory,
    condition_type_factory,
    decision_factory,
    tenant_factory,
    tenant_contact_factory,
    contact_factory,
):
    condition_type = condition_type_factory(name="Condition Type 1")
    lease = lease_factory()
    decision = decision_factory(
        lease=lease,
        reference_number="Decision 1",
    )
    tenant = tenant_factory(
        lease=lease,
        share_numerator=1,
        share_denominator=1,
    )
    contact = contact_factory(
        first_name="John",
        last_name="Doe",
    )
    tenant_contact_factory(
        tenant=tenant,
        contact=contact,
        type="tenant",
        start_date=timezone.now(),
        end_date=timezone.now() + datetime.timedelta(days=123),
    )
    condition = condition_factory(
        decision=decision,
        type=condition_type,
        supervision_date=timezone.now() + datetime.timedelta(days=1),
    )
    return {
        "condition_type": condition_type,
        "lease": lease,
        "decision": decision,
        "tenant": tenant,
        "contact": contact,
        "condition": condition,
    }


@pytest.mark.parametrize("setup_data_key", ["decision", "lease"])
@pytest.mark.django_db
def test_deleted_related_objects(setup_data, setup_data_key):
    report = DecisionConditionsReport()
    input_data = {
        "service_unit": [setup_data.get("lease").service_unit],
        "start_date": timezone.now().date(),
        "end_date": (timezone.now() + datetime.timedelta(days=2)).date(),
        "condition_type": setup_data["condition_type"],
        "supervision_exists": "True",
    }
    data = report.get_data(input_data)
    assert setup_data["condition"] in data

    setup_data[setup_data_key].delete()
    data = report.get_data(input_data)
    assert (
        setup_data["condition"] not in data
    ), f"Condition appears when {setup_data_key} is deleted"
