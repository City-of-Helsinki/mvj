import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.enums import DueDatesType, RentAdjustmentAmountType, RentAdjustmentType, RentCycle, RentType
from leasing.models import Lease


@pytest.mark.django_db
@pytest.mark.parametrize("end_date,expected_status_code,expected_count", [
    (None, 200, 1),
    ("1999-01-01", 400, 0),
    ("2019-01-01", 400, 0),
    ("2025-01-01", 400, 0),
    ("2030-01-01", 400, 0),
])
def test_create_total_amount_adjustment(django_db_setup, admin_client, lease_test_data, rent_factory, decision_factory,
                                        end_date, expected_status_code, expected_count):
    lease = lease_test_data['lease']

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    decision = decision_factory(lease=lease)

    data = {
        "rents": [
            {
                "id": rent.id,
                "type": RentType.FIXED.value,
                "rent_adjustments": [
                    {
                        "type": "discount",
                        "intended_use": 1,
                        "start_date": None,
                        "end_date": end_date,
                        "full_amount": 2000,
                        "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL.value,
                        "decision": decision.id,
                    },
                ],
            },
        ],
    }

    url = reverse('lease-detail', kwargs={
        'pk': lease.id
    })
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == expected_status_code, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=lease.id)

    assert len(lease.rents.first().rent_adjustments.all()) == expected_count


@pytest.mark.django_db
@pytest.mark.parametrize("end_date,expected_status_code,expected_count", [
    (None, 200, 1),
    ("1999-01-01", 400, 1),
    ("2019-01-01", 400, 1),
    ("2025-01-01", 400, 1),
    ("2030-01-01", 400, 1),
])
def test_update_total_amount_adjustment(django_db_setup, admin_client, lease_test_data, rent_factory, decision_factory,
                                        rent_adjustment_factory, end_date, expected_status_code, expected_count):
    lease = lease_test_data['lease']

    rent = rent_factory(
        lease=lease,
        type=RentType.FIXED,
        cycle=RentCycle.JANUARY_TO_DECEMBER,
        due_dates_type=DueDatesType.FIXED,
        due_dates_per_year=1,
    )

    decision = decision_factory(lease=lease)

    rent_adjustment = rent_adjustment_factory(
        rent=rent,
        type=RentAdjustmentType.DISCOUNT,
        decision=decision,
        intended_use_id=1,
        start_date=None,
        end_date=None,
        full_amount=12345,
        amount_type=RentAdjustmentAmountType.AMOUNT_TOTAL,
    )

    data = {
        "rents": [
            {
                "id": rent.id,
                "type": RentType.FIXED.value,
                "rent_adjustments": [
                    {
                        "id": rent_adjustment.id,
                        "type": "discount",
                        "intended_use": 1,
                        "end_date": end_date,
                        "amount_type": RentAdjustmentAmountType.AMOUNT_TOTAL.value,
                        "decision": decision.id,
                    },
                ],
            },
        ],
    }

    url = reverse('lease-detail', kwargs={
        'pk': lease.id
    })
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == expected_status_code, '%s %s' % (response.status_code, response.data)

    lease = Lease.objects.get(pk=lease.id)

    assert len(lease.rents.first().rent_adjustments.all()) == expected_count
    assert lease.rents.first().rent_adjustments.first().end_date is None
