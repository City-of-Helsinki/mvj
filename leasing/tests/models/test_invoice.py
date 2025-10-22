import datetime
import json
from decimal import Decimal

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from leasing.enums import ContactType, InvoiceState, InvoiceType
from leasing.models import Invoice, ReceivableType, ServiceUnit, Vat
from leasing.models.invoice import InvoiceSet
from leasing.models.tenant import TenantContactType


@pytest.mark.django_db
def test_invoice_number_must_be_unique(
    service_unit_factory, lease_factory, contact_factory, invoice_factory
):
    service_unit = service_unit_factory()

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
        service_unit=service_unit,
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        service_unit=service_unit,
    )
    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        service_unit=service_unit,
    )

    invoice.number = 1
    invoice.save()

    with pytest.raises(IntegrityError):
        invoice2.number = 1
        invoice2.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invoice_number_sequence_name, expected",
    [
        ["use_default_service_unit", 1000000],
        [None, 1000000],
        ["", 1000000],
        ["new_name", 1],
        ["another", 1],
    ],
)
def test_invoice_generate_number(
    service_unit_factory,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_number_sequence_name,
    expected,
):
    if invoice_number_sequence_name == "use_default_service_unit":
        service_unit = ServiceUnit.objects.get(pk=1)
    else:
        service_unit = service_unit_factory(
            invoice_number_sequence_name=invoice_number_sequence_name
        )

    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=5,
        notice_period_id=1,
        service_unit=service_unit,
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
    )

    assert invoice.generate_number() == expected


@pytest.mark.django_db
def test_create_credit_invoice_full(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice.create_credit_invoice()

    assert invoice.outstanding_amount == Decimal(0)

    credit_note = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note.type == InvoiceType.CREDIT_NOTE
    assert credit_note.lease == lease
    assert credit_note.recipient == contact
    assert credit_note.rows.all().count() == 1
    assert credit_note.billing_period_start_date == billing_period_start_date
    assert credit_note.billing_period_end_date == billing_period_end_date
    assert credit_note.billed_amount == Decimal(0)

    credit_note_row = credit_note.rows.first()

    assert credit_note_row.amount == pytest.approx(Decimal("123.45"))
    assert credit_note_row.receivable_type == receivable_type

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.REFUNDED


@pytest.mark.django_db
def test_create_credit_invoice_fails(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        type=InvoiceType.CREDIT_NOTE,
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    with pytest.raises(RuntimeError) as e:
        invoice.create_credit_invoice()

    assert (
        str(e.value)
        == 'Can not credit invoice with the type "credit_note". Only type "charge" allowed.'
    )

    with pytest.raises(Invoice.DoesNotExist):
        Invoice.objects.get(credited_invoice=invoice)


@pytest.mark.django_db
def test_create_credit_invoice_full_two_rows(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice.create_credit_invoice()

    credit_note = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note.type == InvoiceType.CREDIT_NOTE
    assert credit_note.lease == lease
    assert credit_note.recipient == contact
    assert credit_note.rows.all().count() == 2
    assert credit_note.billing_period_start_date == billing_period_start_date
    assert credit_note.billing_period_end_date == billing_period_end_date
    assert credit_note.billed_amount == Decimal(0)

    credit_note_row = credit_note.rows.filter(receivable_type=receivable_type).first()

    assert credit_note_row.amount == pytest.approx(Decimal("123.45"))
    assert credit_note_row.receivable_type == receivable_type

    credit_note_row2 = credit_note.rows.filter(receivable_type=receivable_type2).first()

    assert credit_note_row2.amount == pytest.approx(Decimal(70))
    assert credit_note_row2.receivable_type == receivable_type2

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.REFUNDED


@pytest.mark.django_db
def test_create_credit_invoice_one_row_full(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice.create_credit_invoice(row_ids=[invoice_row2.id])

    credit_note = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note.type == InvoiceType.CREDIT_NOTE
    assert credit_note.lease == lease
    assert credit_note.recipient == contact
    assert credit_note.rows.all().count() == 1
    assert credit_note.billing_period_start_date == billing_period_start_date
    assert credit_note.billing_period_end_date == billing_period_end_date
    assert credit_note.billed_amount == Decimal(0)

    credit_note_row = credit_note.rows.first()

    assert credit_note_row.amount == pytest.approx(Decimal(70))
    assert credit_note_row.receivable_type == receivable_type2

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.OPEN


@pytest.mark.django_db
def test_create_credit_invoice_one_row_partly(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice.create_credit_invoice(row_ids=[invoice_row2.id], amount=20)

    assert invoice.outstanding_amount == Decimal("173.45")

    credit_note = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note.type == InvoiceType.CREDIT_NOTE
    assert credit_note.lease == lease
    assert credit_note.recipient == contact
    assert credit_note.rows.all().count() == 1
    assert credit_note.billing_period_start_date == billing_period_start_date
    assert credit_note.billing_period_end_date == billing_period_end_date
    assert credit_note.billed_amount == Decimal(0)

    credit_note_row = credit_note.rows.first()

    assert credit_note_row.amount == pytest.approx(Decimal(20))
    assert credit_note_row.receivable_type == receivable_type2

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.OPEN


@pytest.mark.django_db
def test_create_credit_invoice_one_row_too_much(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row2 = invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    with pytest.raises(RuntimeError) as e:
        invoice.create_credit_invoice(row_ids=[invoice_row2.id], amount=200)

    assert str(e.value) == "Cannot credit more than invoice row amount"


@pytest.mark.django_db
def test_create_credit_invoice_full_one_receivable_type(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice.create_credit_invoice(receivable_type=receivable_type2)

    assert invoice.outstanding_amount == Decimal("123.45")

    credit_note = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note.type == InvoiceType.CREDIT_NOTE
    assert credit_note.lease == lease
    assert credit_note.recipient == contact
    assert credit_note.rows.all().count() == 1
    assert credit_note.billing_period_start_date == billing_period_start_date
    assert credit_note.billing_period_end_date == billing_period_end_date
    assert credit_note.billed_amount == Decimal(0)

    credit_note_row = credit_note.rows.first()

    assert credit_note_row.amount == pytest.approx(Decimal(70))
    assert credit_note_row.receivable_type == receivable_type2

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.OPEN


@pytest.mark.django_db
def test_create_credit_invoiceset_fails(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice_set = invoice_set_factory(
        lease=lease,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    invoice = invoice_factory(
        type=InvoiceType.CREDIT_NOTE,
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice2 = invoice_factory(
        type=InvoiceType.CREDIT_NOTE,
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(150),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    with pytest.raises(RuntimeError) as e:
        invoice_set.create_credit_invoiceset()

    assert (
        str(e.value)
        == 'No refundable invoices found (no invoices with the type "charge" found)'
    )

    assert InvoiceSet.objects.count() == 1


@pytest.mark.django_db
def test_create_credit_invoiceset_full(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice_set = invoice_set_factory(
        lease=lease,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("193.45"),
        billed_amount=Decimal("193.45"),
        outstanding_amount=Decimal("193.45"),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal("123.45"),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(150),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_set.create_credit_invoiceset()

    assert InvoiceSet.objects.count() == 2

    credit_note_invoiceset = InvoiceSet.objects.first()
    assert credit_note_invoiceset.lease == lease
    assert credit_note_invoiceset.billing_period_start_date == billing_period_start_date
    assert credit_note_invoiceset.billing_period_end_date == billing_period_end_date

    credit_note1 = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note1.type == InvoiceType.CREDIT_NOTE
    assert credit_note1.lease == lease
    assert credit_note1.recipient == contact
    assert credit_note1.rows.count() == 2
    assert credit_note1.billing_period_start_date == billing_period_start_date
    assert credit_note1.billing_period_end_date == billing_period_end_date
    assert credit_note1.billed_amount == Decimal(0)

    credit_note_row1 = credit_note1.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row1.amount == pytest.approx(Decimal("123.45"))

    credit_note_row2 = credit_note1.rows.filter(
        receivable_type=receivable_type2
    ).first()
    assert credit_note_row2.amount == pytest.approx(Decimal(70))

    credit_note2 = Invoice.objects.get(credited_invoice=invoice2)

    assert credit_note2.type == InvoiceType.CREDIT_NOTE
    assert credit_note2.lease == lease
    assert credit_note2.recipient == contact
    assert credit_note2.rows.count() == 2
    assert credit_note2.billing_period_start_date == billing_period_start_date
    assert credit_note2.billing_period_end_date == billing_period_end_date
    assert credit_note2.billed_amount == Decimal(0)

    credit_note_row3 = credit_note2.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row3.amount == pytest.approx(Decimal(150))

    credit_note_row4 = credit_note2.rows.filter(
        receivable_type=receivable_type2
    ).first()
    assert credit_note_row4.amount == pytest.approx(Decimal(50))

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.REFUNDED
    assert Invoice.objects.get(pk=invoice2.id).state == InvoiceState.REFUNDED


@pytest.mark.django_db
def test_create_credit_invoiceset_receivable_type(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
    tenant_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name2", last_name="Last name2", type=ContactType.PERSON
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=2)

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice_set = invoice_set_factory(
        lease=lease,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(170),
        billed_amount=Decimal(170),
        outstanding_amount=Decimal(170),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(70),
    )

    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(150),
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_set.create_credit_invoiceset(receivable_type=receivable_type)

    assert InvoiceSet.objects.count() == 2

    credit_note_invoiceset = InvoiceSet.objects.first()
    assert credit_note_invoiceset.lease == lease
    assert credit_note_invoiceset.billing_period_start_date == billing_period_start_date
    assert credit_note_invoiceset.billing_period_end_date == billing_period_end_date

    credit_note1 = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note1.type == InvoiceType.CREDIT_NOTE
    assert credit_note1.lease == lease
    assert credit_note1.recipient == contact
    assert credit_note1.rows.count() == 1
    assert credit_note1.billing_period_start_date == billing_period_start_date
    assert credit_note1.billing_period_end_date == billing_period_end_date
    assert credit_note1.billed_amount == Decimal(0)

    credit_note_row1 = credit_note1.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row1.amount == pytest.approx(Decimal(100))

    credit_note2 = Invoice.objects.get(credited_invoice=invoice2)

    assert credit_note2.type == InvoiceType.CREDIT_NOTE
    assert credit_note2.lease == lease
    assert credit_note2.recipient == contact2
    assert credit_note2.rows.count() == 1
    assert credit_note2.billing_period_start_date == billing_period_start_date
    assert credit_note2.billing_period_end_date == billing_period_end_date
    assert credit_note2.billed_amount == Decimal(0)

    credit_note_row2 = credit_note2.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row2.amount == pytest.approx(Decimal(150))


@pytest.mark.django_db
def test_create_credit_invoiceset_receivable_type_partly(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
    tenant_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name2", last_name="Last name2", type=ContactType.PERSON
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=3, share_denominator=6)
    tenant2 = tenant_factory(lease=lease, share_numerator=1, share_denominator=6)
    tenant3 = tenant_factory(lease=lease, share_numerator=2, share_denominator=6)

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice_set = invoice_set_factory(
        lease=lease,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(400),
        billed_amount=Decimal(400),
        outstanding_amount=Decimal(400),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(300),
    )

    invoice_row_factory(
        invoice=invoice,
        tenant=tenant1,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal(400),
        billed_amount=Decimal(400),
        outstanding_amount=Decimal(400),
        recipient=contact2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant3,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_row_factory(
        invoice=invoice2,
        tenant=tenant3,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_set.create_credit_invoiceset_for_amount(
        receivable_type=receivable_type, amount=200
    )

    assert InvoiceSet.objects.count() == 2

    credit_note_invoiceset = InvoiceSet.objects.first()
    assert credit_note_invoiceset.lease == lease
    assert credit_note_invoiceset.billing_period_start_date == billing_period_start_date
    assert credit_note_invoiceset.billing_period_end_date == billing_period_end_date

    credit_note1 = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note1.type == InvoiceType.CREDIT_NOTE
    assert credit_note1.lease == lease
    assert credit_note1.recipient == contact
    assert credit_note1.rows.count() == 1
    assert credit_note1.billing_period_start_date == billing_period_start_date
    assert credit_note1.billing_period_end_date == billing_period_end_date
    assert credit_note1.billed_amount == Decimal(0)

    credit_note_row1 = credit_note1.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row1.amount == pytest.approx(Decimal(100))

    credit_note2 = Invoice.objects.get(credited_invoice=invoice2)

    assert credit_note2.type == InvoiceType.CREDIT_NOTE
    assert credit_note2.lease == lease
    assert credit_note2.recipient == contact2
    assert credit_note2.rows.count() == 2
    assert credit_note2.rows.filter(tenant=tenant2).count() == 1
    assert credit_note2.rows.filter(tenant=tenant3).count() == 1
    assert credit_note2.billing_period_start_date == billing_period_start_date
    assert credit_note2.billing_period_end_date == billing_period_end_date
    assert credit_note2.billed_amount == Decimal(0)

    credit_note_row2 = credit_note2.rows.filter(tenant=tenant2).first()
    assert credit_note_row2.amount == pytest.approx(Decimal("33.33"))

    credit_note_row3 = credit_note2.rows.filter(tenant=tenant3).first()
    assert credit_note_row3.amount == pytest.approx(Decimal("66.67"))


@pytest.mark.django_db
def test_create_credit_invoiceset_receivable_type_partly_no_tenants(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_set_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )
    contact2 = contact_factory(
        first_name="First name2", last_name="Last name2", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice_set = invoice_set_factory(
        lease=lease,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(300),
        billed_amount=Decimal(300),
        outstanding_amount=Decimal(300),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    receivable_type = ReceivableType.objects.get(pk=1)
    receivable_type2 = ReceivableType.objects.get(pk=2)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice2 = invoice_factory(
        lease=lease,
        total_amount=Decimal(300),
        billed_amount=Decimal(300),
        outstanding_amount=Decimal(300),
        recipient=contact2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        invoiceset=invoice_set,
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(100),
    )

    invoice_row_factory(
        invoice=invoice2,
        receivable_type=receivable_type2,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(50),
    )

    invoice_set.create_credit_invoiceset_for_amount(
        receivable_type=receivable_type, amount=200
    )

    assert InvoiceSet.objects.count() == 2

    credit_note_invoiceset = InvoiceSet.objects.first()
    assert credit_note_invoiceset.lease == lease
    assert credit_note_invoiceset.billing_period_start_date == billing_period_start_date
    assert credit_note_invoiceset.billing_period_end_date == billing_period_end_date

    credit_note1 = Invoice.objects.get(credited_invoice=invoice)

    assert credit_note1.type == InvoiceType.CREDIT_NOTE
    assert credit_note1.lease == lease
    assert credit_note1.recipient == contact
    assert credit_note1.rows.count() == 1
    assert credit_note1.billing_period_start_date == billing_period_start_date
    assert credit_note1.billing_period_end_date == billing_period_end_date
    assert credit_note1.billed_amount == Decimal(0)

    credit_note_row1 = credit_note1.rows.filter(receivable_type=receivable_type).first()
    assert credit_note_row1.amount == pytest.approx(Decimal("66.67"))

    credit_note2 = Invoice.objects.get(credited_invoice=invoice2)

    assert credit_note2.type == InvoiceType.CREDIT_NOTE
    assert credit_note2.lease == lease
    assert credit_note2.recipient == contact2
    assert credit_note2.rows.count() == 2
    assert credit_note2.rows.filter(receivable_type=receivable_type).count() == 2
    assert credit_note2.billing_period_start_date == billing_period_start_date
    assert credit_note2.billing_period_end_date == billing_period_end_date
    assert credit_note2.billed_amount == Decimal(0)

    credit_note_row2 = credit_note2.rows.first()
    assert credit_note_row2.amount == pytest.approx(Decimal("66.67"))

    credit_note_row3 = credit_note2.rows.last()
    assert credit_note_row3.amount == pytest.approx(Decimal("66.67"))


@pytest.mark.django_db
def test_create_credit_invoice_refunded_in_parts(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice.create_credit_invoice(amount=100)
    assert invoice.outstanding_amount == Decimal(100)

    invoice.create_credit_invoice(amount=100)
    assert invoice.outstanding_amount == Decimal(0)

    credit_notes = Invoice.objects.filter(credited_invoice=invoice)

    assert credit_notes.count() == 2

    assert Invoice.objects.get(pk=invoice.id).state == InvoiceState.REFUNDED


@pytest.mark.django_db
def test_create_credit_invoice_too_much(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    with pytest.raises(RuntimeError) as e:
        invoice.create_credit_invoice(amount=205)

    assert str(e.value) == "Cannot credit more than invoice row amount"


@pytest.mark.django_db
def test_create_credit_invoice_too_much_already_credited(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice.create_credit_invoice(amount=100)
    assert invoice.outstanding_amount == Decimal(100)

    with pytest.raises(RuntimeError) as e:
        invoice.create_credit_invoice(amount=105)

    assert (
        str(e.value)
        == "Cannot credit more than total amount minus already credited amount"
    )


@pytest.mark.django_db
def test_create_credit_invoice_full_already_credited_partly(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice.create_credit_invoice(amount=50)
    assert invoice.outstanding_amount == Decimal(150)

    credit_note = invoice.create_credit_invoice()

    assert credit_note.total_amount == Decimal(150)


@pytest.mark.django_db
def test_outstanding_amount_after_partial_payment(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(100),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(100)
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_outstanding_amount_after_one_full_payment(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(200),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_outstanding_amount_after_multiple_payments_partial(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(20),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(30),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(150)
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_outstanding_amount_after_multiple_payments_full(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=Decimal(200),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(100),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(100),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_outstanding_amount_with_collection_charge(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=None,
        collection_charge=Decimal(5),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(205)
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_outstanding_amount_with_collection_charge_one_payment(
    django_db_setup,
    lease_factory,
    contact_factory,
    invoice_factory,
    invoice_row_factory,
    invoice_payment_factory,
):
    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=7, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(200),
        billed_amount=Decimal(200),
        outstanding_amount=None,
        collection_charge=Decimal(5),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    receivable_type = ReceivableType.objects.get(pk=1)

    invoice_row_factory(
        invoice=invoice,
        receivable_type=receivable_type,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
        amount=Decimal(200),
    )

    invoice_payment_factory(
        invoice=invoice,
        paid_amount=Decimal(100),
        paid_date=datetime.date(year=2018, month=1, day=1),
    )

    invoice.update_amounts()

    assert invoice.outstanding_amount == Decimal(105)
    assert invoice.state == InvoiceState.OPEN


@pytest.mark.django_db
def test_calculate_penalty_amount(
    django_db_setup, lease_factory, contact_factory, invoice_factory
):
    calculation_date = datetime.date(year=2018, month=9, day=6)

    lease = lease_factory(
        type_id=1, municipality_id=1, district_id=5, notice_period_id=1
    )

    contact = contact_factory(
        first_name="First name", last_name="Last name", type=ContactType.PERSON
    )

    billing_period_start_date = datetime.date(year=2017, month=1, day=1)
    billing_period_end_date = datetime.date(year=2017, month=12, day=31)

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal(500),
        billed_amount=Decimal(500),
        outstanding_amount=Decimal(100),
        due_date=datetime.date(year=2017, month=1, day=1),
        recipient=contact,
        billing_period_start_date=billing_period_start_date,
        billing_period_end_date=billing_period_end_date,
    )

    penalty_interest_data = invoice.calculate_penalty_interest(
        calculation_date=calculation_date
    )

    assert penalty_interest_data["interest_start_date"] == datetime.date(
        year=2017, month=1, day=2
    )
    assert penalty_interest_data["interest_end_date"] == calculation_date
    assert penalty_interest_data["total_interest_amount"].compare(Decimal("11.76")) == 0
    assert len(penalty_interest_data["interest_periods"]) == 4


@pytest.mark.django_db
def test_is_same_recipient_and_tenants(django_db_setup, invoices_test_data):
    assert invoices_test_data["invoice1"].is_same_recipient_and_tenants(
        invoices_test_data["invoice2"]
    )


@pytest.mark.django_db
def test_is_same_recipient_and_tenants_dict(django_db_setup, invoices_test_data):
    invoice_keys = [
        "type",
        "lease",
        "recipient",
        "due_date",
        "billing_period_start_date",
        "billing_period_end_date",
        "total_amount",
        "billed_amount",
        "state",
    ]
    invoice2_dict = {}
    for key in invoice_keys:
        invoice2_dict[key] = getattr(invoices_test_data["invoice2"], key)

    invoice2_dict["rows"] = []
    invoice_row_keys = [
        "tenant",
        "receivable_type",
        "billing_period_start_date",
        "billing_period_end_date",
        "amount",
    ]
    for row in invoices_test_data["invoice2"].rows.all():
        invoice_row_dict = {}
        for key in invoice_row_keys:
            invoice_row_dict[key] = getattr(row, key)

        invoice2_dict["rows"].append(invoice_row_dict)

    assert invoices_test_data["invoice1"].is_same_recipient_and_tenants(invoice2_dict)


@pytest.mark.django_db
def test_is_same_recipient_and_tenants2(django_db_setup, invoices_test_data):
    invoice_row = invoices_test_data["invoice2"].rows.first()
    invoice_row.tenant = invoices_test_data["tenant2"]
    invoice_row.save()

    assert (
        invoices_test_data["invoice1"].is_same_recipient_and_tenants(
            invoices_test_data["invoice2"]
        )
        is False
    )


@pytest.mark.django_db
def test_is_same_recipient_and_tenants3(
    django_db_setup, invoices_test_data, contact_factory
):
    contact3 = contact_factory(
        first_name="First name 3", last_name="Last name 3", type=ContactType.PERSON
    )

    invoice1 = invoices_test_data["invoice1"]
    invoice1.recipient = contact3
    invoice1.save()

    assert (
        invoices_test_data["invoice1"].is_same_recipient_and_tenants(
            invoices_test_data["invoice2"]
        )
        is False
    )


@pytest.mark.django_db
def test_is_same_recipient_and_tenants4(
    django_db_setup, invoices_test_data, contact_factory
):
    assert invoices_test_data["invoice1"].is_same_recipient_and_tenants(
        invoices_test_data["invoice2"]
    )

    invoices_test_data["invoice1"].rows.all().delete()

    assert (
        invoices_test_data["invoice1"].is_same_recipient_and_tenants(
            invoices_test_data["invoice2"]
        )
        is False
    )

    invoices_test_data["invoice2"].rows.all().delete()

    assert invoices_test_data["invoice1"].is_same_recipient_and_tenants(
        invoices_test_data["invoice2"]
    )


@pytest.mark.django_db
def test_create_invoice_zero_amount_is_set_to_status_paid(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    # Create invoice with API because invoice_factory sets state to OPEN (which is fine as a default)
    data = {
        "lease": lease.id,
        "tenant": tenant1.id,
        "due_date": "2019-01-01",
        "rows": [{"amount": Decimal(0), "receivable_type": 1}],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    invoice = Invoice.objects.get(pk=response.data["id"])
    assert invoice.total_amount == Decimal(0)
    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_create_invoice_zero_row_sum_is_set_to_status_paid(
    django_db_setup,
    admin_client,
    lease_factory,
    tenant_factory,
    tenant_rent_share_factory,
    contact_factory,
    tenant_contact_factory,
):
    lease = lease_factory(
        type_id=1,
        municipality_id=1,
        district_id=1,
        notice_period_id=1,
        start_date=datetime.date(year=2000, month=1, day=1),
        invoicing_enabled_at=datetime.datetime(year=2000, month=1, day=1),
    )

    tenant1 = tenant_factory(lease=lease, share_numerator=1, share_denominator=1)
    tenant_rent_share_factory(
        tenant=tenant1, intended_use_id=1, share_numerator=1, share_denominator=1
    )
    contact1 = contact_factory(
        first_name="First name 1", last_name="Last name 1", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.TENANT,
        tenant=tenant1,
        contact=contact1,
        start_date=datetime.date(year=2000, month=1, day=1),
    )
    contact2 = contact_factory(
        first_name="First name 2", last_name="Last name 2", type=ContactType.PERSON
    )
    tenant_contact_factory(
        type=TenantContactType.BILLING,
        tenant=tenant1,
        contact=contact2,
        start_date=datetime.date(year=2000, month=1, day=1),
    )

    # Create invoice with API because invoice_factory sets state to OPEN (which is fine as a default)
    data = {
        "lease": lease.id,
        "tenant": tenant1.id,
        "due_date": "2019-01-01",
        "rows": [
            {"amount": Decimal(100), "receivable_type": 1},
            {"amount": Decimal(-100), "receivable_type": 1},
        ],
    }

    url = reverse("v1:invoice-list")
    response = admin_client.post(
        url,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )

    assert response.status_code == 201, "%s %s" % (response.status_code, response.data)
    invoice = Invoice.objects.get(pk=response.data["id"])
    assert invoice.total_amount == Decimal(0)
    assert invoice.outstanding_amount == Decimal(0)
    assert invoice.state == InvoiceState.PAID


@pytest.mark.django_db
def test_invoice_get_vat_if_subject_to_vat(lease_factory, invoice_factory):
    # These tests rely on existing VAT's defined in a fixture.
    # What is being tested is the switch to new VAT on 2024-09-01.
    # And the logic to determine which VAT to use in each case.
    lease_not_subjet_to_vat = lease_factory(is_subject_to_vat=False)
    total_amount = Decimal(100)
    invoice_kwargs = {
        "total_amount": total_amount,
        "billed_amount": Decimal(0),
    }
    invoice_without_vat: Invoice = invoice_factory(
        lease=lease_not_subjet_to_vat,
        **invoice_kwargs,
    )
    vat = invoice_without_vat.get_vat_if_subject_to_vat(
        datetime.date(year=2024, month=8, day=30), total_amount
    )
    assert vat is None, "Should not return VAT if lease is not subject to VAT"

    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    billing_period_end_date = datetime.date(year=2024, month=8, day=30)
    payment_date = datetime.date(year=2024, month=9, day=1)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=billing_period_end_date,
        **invoice_kwargs,
    )
    vat = invoice_with_vat.get_vat_if_subject_to_vat(payment_date, total_amount)
    vat_of_billing_period_end = Vat.objects.get_for_date(billing_period_end_date)
    assert (
        vat == vat_of_billing_period_end
    ), "Should return VAT based on billing_period_end_date"

    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    invoicing_date = datetime.date(year=2024, month=9, day=1)
    payment_date = datetime.date(year=2024, month=9, day=1)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=None,
        invoicing_date=invoicing_date,
        **invoice_kwargs,
    )
    vat = invoice_with_vat.get_vat_if_subject_to_vat(payment_date, total_amount)
    vat_of_invoicing_date = Vat.objects.get_for_date(invoicing_date)
    assert vat == vat_of_invoicing_date, "Should return VAT based on invoicing_date"

    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    payment_date = datetime.date(year=2024, month=9, day=1)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=None,
        invoicing_date=None,
        **invoice_kwargs,
    )
    vat = invoice_with_vat.get_vat_if_subject_to_vat(payment_date, total_amount)
    vat_for_today = Vat.objects.get_for_date(timezone.now().date())
    assert (
        vat == vat_for_today
    ), "Should return VAT of today when no invoicing_date or billing_period_end_date is set"

    # Special case: payment is paid fully in advance before VAT changes.
    # In this case VAT date is the payment date.
    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    billing_period_end_date = datetime.date(year=2024, month=8, day=30)
    payment_date = datetime.date(year=2024, month=8, day=30)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=billing_period_end_date,
        invoicing_date=None,
        **invoice_kwargs,
    )
    vat = invoice_with_vat.get_vat_if_subject_to_vat(payment_date, total_amount)
    vat_payment_date = Vat.objects.get_for_date(payment_date)
    assert (
        vat == vat_payment_date
    ), "Should return VAT of payment_date when payment is paid fully in advance before VAT change"

    # Payment is not paid fully but in advance before VAT changes.
    # In this case VAT date is billing_period_end_date.
    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    billing_period_end_date = datetime.date(year=2024, month=9, day=1)
    payment_date = datetime.date(year=2024, month=8, day=30)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=billing_period_end_date,
        invoicing_date=None,
        **invoice_kwargs,
    )
    payment_not_full = total_amount - Decimal(1)
    vat = invoice_with_vat.get_vat_if_subject_to_vat(payment_date, payment_not_full)
    vat_of_billing_period_end = Vat.objects.get_for_date(billing_period_end_date)
    assert (
        vat == vat_of_billing_period_end
    ), "Should return VAT of billing_period_end_date when payment is NOT paid fully in advance before VAT change"

    # Special case: payment is _overpaid_ (more paid than on invoice) in advance before VAT changes.
    # In this case VAT date is the payment date.
    lease_subject_to_vat = lease_factory(is_subject_to_vat=True)
    billing_period_end_date = datetime.date(year=2024, month=8, day=30)
    payment_date = datetime.date(year=2024, month=8, day=30)
    invoice_with_vat: Invoice = invoice_factory(
        lease=lease_subject_to_vat,
        billing_period_end_date=billing_period_end_date,
        invoicing_date=None,
        **invoice_kwargs,
    )
    payment_over_total_amount = total_amount + Decimal(100)
    vat = invoice_with_vat.get_vat_if_subject_to_vat(
        payment_date, payment_over_total_amount
    )
    vat_payment_date = Vat.objects.get_for_date(payment_date)
    assert (
        vat == vat_payment_date
    ), "Overpayment in advance should not affect the VAT, and paymend date should be used to determine VAT"
