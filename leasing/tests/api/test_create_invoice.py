import datetime
import json
from decimal import Decimal

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType, TenantContactType
from leasing.models import Invoice


@pytest.mark.django_db
def test_create_invoice(django_db_setup, admin_client, lease_factory, tenant_factory,
                        tenant_rent_share_factory, contact_factory, tenant_contact_factory):
    lease = lease_factory(type_id=1, municipality_id=1, district_id=1, notice_period_id=1,
                          start_date=datetime.date(year=2000, month=1, day=1), is_invoicing_enabled=True)

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1)
    contact1 = contact_factory(first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON)
    tenant_contact_factory(type=TenantContactType.TENANT, tenant=tenant1, contact=contact1,
                           start_date=datetime.date(year=2000, month=1, day=1))

    data = {
        'lease': lease.id,
        'recipient': contact1.id,
        'due_date': '2019-01-01',
        'rows': [
            {
                'amount': Decimal(10),
                'receivable_type': 1,
            }
        ],
    }

    url = reverse('invoice-list')
    response = admin_client.post(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 201, '%s %s' % (response.status_code, response.data)

    invoice = Invoice.objects.get(pk=response.data['id'])

    assert invoice.invoicing_date == timezone.now().date()
    assert invoice.outstanding_amount == Decimal(10)
