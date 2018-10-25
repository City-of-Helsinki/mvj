import json
from decimal import Decimal

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

from leasing.enums import ContactType, InvoiceType
from leasing.models import Invoice
from leasing.models.invoice import InvoiceRow


@pytest.mark.django_db
def test_patch_invoice_change_one_row_amount(django_db_setup, admin_client, lease_test_data, contact_factory,
                                             invoice_factory, invoice_row_factory):
    lease = lease_test_data['lease']

    contact = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(123.45),
        billed_amount=Decimal(123.45),
        outstanding_amount=Decimal(123.45),
        recipient=contact,
    )

    invoice_row = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(123.45),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row.id,
                "receivable_type": invoice_row.receivable_type_id,
                "amount": 100,
            },
        ],
    }

    url = reverse('invoice-detail', kwargs={'pk': invoice.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    invoice_row = InvoiceRow.objects.get(pk=invoice_row.id)

    assert invoice_row.amount == Decimal(100)

    invoice = Invoice.objects.get(pk=response.data['id'])

    assert invoice.billed_amount == Decimal(100)
    assert invoice.outstanding_amount == Decimal(100)
    assert invoice.total_amount == Decimal(100)


@pytest.mark.django_db
def test_patch_invoice_change_other_row_amount(django_db_setup, admin_client, lease_test_data, contact_factory,
                                               invoice_factory, invoice_row_factory):
    lease = lease_test_data['lease']

    contact = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(250),
        billed_amount=Decimal(250),
        recipient=contact,
    )

    invoice_row1 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(100),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(150),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "amount": 100,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "amount": 80,
            },
        ],
    }

    url = reverse('invoice-detail', kwargs={'pk': invoice.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    invoice_row1 = InvoiceRow.objects.get(pk=invoice_row1.id)
    assert invoice_row1.amount == Decimal(100)
    invoice_row2 = InvoiceRow.objects.get(pk=invoice_row2.id)
    assert invoice_row2.amount == Decimal(80)

    invoice = Invoice.objects.get(pk=response.data['id'])

    assert invoice.billed_amount == Decimal(180)
    assert invoice.outstanding_amount == Decimal(180)
    assert invoice.total_amount == Decimal(180)


@pytest.mark.django_db
def test_patch_invoice_change_two_row_amount(django_db_setup, admin_client, lease_test_data, contact_factory,
                                             invoice_factory, invoice_row_factory):
    lease = lease_test_data['lease']

    contact = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)

    invoice = invoice_factory(
        lease=lease,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(250),
        billed_amount=Decimal(250),
        recipient=contact,
    )

    invoice_row1 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(100),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(150),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "amount": 50,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "amount": 60,
            },
        ],
    }

    url = reverse('invoice-detail', kwargs={'pk': invoice.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    invoice_row1 = InvoiceRow.objects.get(pk=invoice_row1.id)
    assert invoice_row1.amount == Decimal(50)
    invoice_row2 = InvoiceRow.objects.get(pk=invoice_row2.id)
    assert invoice_row2.amount == Decimal(60)

    invoice = Invoice.objects.get(pk=response.data['id'])

    assert invoice.billed_amount == Decimal(110)
    assert invoice.outstanding_amount == Decimal(110)
    assert invoice.total_amount == Decimal(110)


@pytest.mark.django_db
def test_patch_invoice_with_invoiceset_change_row_amount(django_db_setup, admin_client, lease_test_data,
                                                         contact_factory, invoice_set_factory, invoice_factory,
                                                         invoice_row_factory):
    lease = lease_test_data['lease']

    contact = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)

    invoiceset = invoice_set_factory(lease=lease)

    invoice = invoice_factory(
        lease=lease,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350),
        billed_amount=Decimal(250),
        outstanding_amount=Decimal(250),
        recipient=contact,
    )

    invoice_row1 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(100),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(150),
    )

    invoice2 = invoice_factory(
        lease=lease,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350),
        billed_amount=Decimal(100),
        outstanding_amount=Decimal(100),
        recipient=contact,
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        amount=Decimal(50),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        amount=Decimal(50),
    )

    data = {
        "id": invoice.id,
        "rows": [
            {
                "id": invoice_row1.id,
                "receivable_type": invoice_row1.receivable_type_id,
                "amount": 50,
            },
            {
                "id": invoice_row2.id,
                "receivable_type": invoice_row2.receivable_type_id,
                "amount": 60,
            },
        ],
    }

    url = reverse('invoice-detail', kwargs={'pk': invoice.id})
    response = admin_client.patch(url, data=json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

    assert response.status_code == 200, '%s %s' % (response.status_code, response.data)

    invoice = Invoice.objects.filter(pk=invoice.id).first()

    assert invoice.billed_amount == Decimal(110)
    assert invoice.outstanding_amount == Decimal(110)
    assert invoice.total_amount == Decimal(210)

    invoice2 = Invoice.objects.get(pk=invoice2.id)

    assert invoice2.billed_amount == Decimal(100)
    assert invoice2.outstanding_amount == Decimal(100)
    assert invoice2.total_amount == Decimal(210)


@pytest.mark.django_db
def test_delete_invoice_invoice_in_invoiceset(
        django_db_setup, admin_client, lease_test_data, contact_factory, invoice_set_factory, invoice_factory,
        invoice_row_factory):
    lease = lease_test_data['lease']

    contact = contact_factory(first_name="First name", last_name="Last name", type=ContactType.PERSON)

    invoiceset = invoice_set_factory(lease=lease)

    invoice = invoice_factory(
        lease=lease,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350),
        billed_amount=Decimal(250),
        outstanding_amount=Decimal(250),
        recipient=contact,
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(100),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type_id=1,
        amount=Decimal(150),
    )

    invoice2 = invoice_factory(
        lease=lease,
        invoiceset=invoiceset,
        type=InvoiceType.CHARGE,
        total_amount=Decimal(350),
        billed_amount=Decimal(100),
        outstanding_amount=Decimal(100),
        recipient=contact,
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        amount=Decimal(50),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type_id=1,
        amount=Decimal(50),
    )

    url = reverse('invoice-detail', kwargs={'pk': invoice2.id})
    response = admin_client.delete(url, content_type='application/json')

    assert response.status_code == 204, '%s %s' % (response.status_code, response.data)

    with pytest.raises(Invoice.DoesNotExist):
        Invoice.objects.get(pk=invoice2.id)

    invoice = Invoice.objects.get(pk=invoice.id)

    assert invoice.billed_amount == Decimal(250)
    assert invoice.outstanding_amount == Decimal(250)
    assert invoice.total_amount == Decimal(250)
