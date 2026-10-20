import pytest
from django.core.exceptions import ValidationError

from landuse.models.agreement import LandUseAgreement
from landuse.models.contract import Contract
from landuse.models.party import AgreementParty
from landuse.models.payment_schedule import (
    PaymentSchedule,
    PaymentScheduleStatus,
    PaymentScheduleInstallment,
    PaymentScheduleInstallmentItem,
)
from landuse.models.invoice import Invoice, InvoiceStatus


@pytest.mark.django_db
def test_payment_schedule_validates_related_agreement():
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    other_agreement = LandUseAgreement.objects.create(identifier="M-2026-2")
    party = AgreementParty.objects.create(agreement=other_agreement)
    contract = Contract.objects.create(agreement=agreement)
    schedule = PaymentSchedule(
        agreement=agreement,
        recipient_party=party,
        contract=contract,
    )

    with pytest.raises(ValidationError, match="Recipient party must belong"):
        schedule.full_clean()


@pytest.mark.django_db
def test_payment_schedule_transition_rules():
    agreement = LandUseAgreement.objects.create(identifier="M-2026-1")
    party = AgreementParty.objects.create(agreement=agreement)
    contract = Contract.objects.create(agreement=agreement)
    schedule = PaymentSchedule.objects.create(
        agreement=agreement,
        recipient_party=party,
        contract=contract,
    )

    schedule.submit()
    assert schedule.status == PaymentScheduleStatus.PENDING_APPROVAL

    schedule.reject("Needs correction")
    assert schedule.status == PaymentScheduleStatus.REJECTED
    assert schedule.rejected_reason == "Needs correction"

    schedule.submit()
    schedule.approve()
    assert schedule.status == PaymentScheduleStatus.APPROVED

    with pytest.raises(ValidationError, match="Only pending schedules"):
        schedule.reject("Too late")


@pytest.mark.django_db
def test_approval_creates_linked_invoice_drafts_and_snapshots():
    agreement = LandUseAgreement.objects.create(identifier="MA101-1")
    party = AgreementParty.objects.create(agreement=agreement, name="Test Oy")
    contract = Contract.objects.create(agreement=agreement)
    schedule = PaymentSchedule.objects.create(
        agreement=agreement,
        recipient_party=party,
        contract=contract,
        status=PaymentScheduleStatus.PENDING_APPROVAL,
    )
    installment = PaymentScheduleInstallment.objects.create(
        payment_schedule=schedule,
        installment_sequence_number=1,
        installment_count_total=1,
    )
    PaymentScheduleInstallmentItem.objects.create(
        installment=installment,
        item_type="LAND_USE_COMPENSATION",
        amount="100.00",
    )

    schedule.approve()

    invoice = Invoice.objects.get(source_payment_schedule_installment=installment)
    assert invoice.status == InvoiceStatus.DRAFT
    assert invoice.billed_amount == 100
    assert invoice.items.get().item_type == "LAND_USE_COMPENSATION"
    assert invoice.recipient_snapshot.name == "Test Oy"
