from decimal import Decimal

import pytest
from django.urls import reverse

from leasing.enums import InvoiceType


@pytest.mark.django_db
def test_user_cannot_delete_invoice_from_another_service_unit(
    django_db_setup,
    client,
    lease_test_data,
    service_unit_factory,
    user_factory,
    contact_factory,
    invoice_factory,
):
    lease = lease_test_data["lease"]
    service_unit2 = service_unit_factory()
    user = user_factory(
        username="test_user",
        permissions=["delete_invoice"],
        service_units=[service_unit2],
    )

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123.45),
        billed_amount=Decimal(123.45),
        outstanding_amount=Decimal(123.45),
        recipient=contact_factory(),
    )

    client.force_login(user)

    url = reverse("invoice-detail", kwargs={"pk": invoice.id})
    response = client.delete(url)

    assert response.status_code == 403, "%s %s" % (response.status_code, response.data)
