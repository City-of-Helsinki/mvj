import json
from decimal import Decimal

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType, InvoiceType
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow, InvoiceSet


@pytest.mark.django_db
def test_invoice_credit_rounding(
    django_db_setup,
    assert_count_equal,
    admin_client,
    lease_test_data,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    tenant_factory,
):
    lease = lease_test_data["lease"]

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(300),
        billed_amount=Decimal(300),
        outstanding_amount=Decimal(300),
        recipient=contact,
        sent_to_sap_at=timezone.now(),
    )

    for i in range(1, 4):
        tenant = tenant_factory(lease=lease, share_numerator=1, share_denominator=3)
        invoice_row_factory(
            invoice=invoice, tenant=tenant, receivable_type_id=1, amount=Decimal(100)
        )

    data = {"receivable_type": 1, "amount": "100"}

    url = reverse("v1:invoice-credit") + "?invoice={}".format(invoice.id)
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    credit_note = Invoice.objects.get(type=InvoiceType.CREDIT_NOTE)

    assert credit_note.total_amount == Decimal(100)
    assert InvoiceRow.objects.filter(invoice=credit_note).aggregate(sum=Sum("amount"))[
        "sum"
    ] == Decimal(100)
    assert_count_equal(
        list(
            InvoiceRow.objects.filter(invoice=credit_note).values_list(
                "amount", flat=True
            )
        ),
        [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")],
    )


@pytest.mark.django_db
def test_invoice_set_credit_rounding(
    django_db_setup,
    assert_count_equal,
    admin_client,
    lease_test_data,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
):
    lease = lease_test_data["lease"]

    invoiceset = invoice_set_factory(lease=lease)

    for i in range(1, 4):
        contact = contact_factory(
            first_name="First name {}".format(i),
            last_name="Last name {}".format(i),
            type=ContactType.PERSON,
        )

        invoice = invoice_factory(
            lease=lease,
            invoiceset=invoiceset,
            type=InvoiceType.CHARGE,
            total_amount=Decimal(300),
            billed_amount=Decimal(100),
            outstanding_amount=Decimal(100),
            recipient=contact,
        )

        invoice_row_factory(invoice=invoice, receivable_type_id=1, amount=Decimal(100))

    data = {"receivable_type": 1, "amount": "100"}

    url = reverse("v1:invoice-set-credit") + "?invoice_set={}".format(invoiceset.id)
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 200, "%s %s" % (response.status_code, response.data)

    credit_invoice_set = InvoiceSet.objects.exclude(id=invoiceset.id).first()

    assert (
        Invoice.objects.filter(
            invoiceset=credit_invoice_set, type=InvoiceType.CREDIT_NOTE
        ).count()
        == 3
    )
    assert Invoice.objects.filter(
        invoiceset=credit_invoice_set, type=InvoiceType.CREDIT_NOTE
    ).aggregate(sum=Sum("total_amount"))["sum"] == Decimal(100)
    assert InvoiceRow.objects.filter(invoice__invoiceset=credit_invoice_set).aggregate(
        sum=Sum("amount")
    )["sum"] == Decimal(100)
    assert_count_equal(
        list(
            InvoiceRow.objects.filter(
                invoice__invoiceset=credit_invoice_set
            ).values_list("amount", flat=True)
        ),
        [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")],
    )
