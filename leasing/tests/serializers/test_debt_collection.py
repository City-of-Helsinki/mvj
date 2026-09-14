import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import ValidationError

from leasing.enums import CollectionStage
from leasing.models.decision import Decision
from leasing.serializers.debt_collection import (
    CollectionCourtDecisionCreateUpdateSerializer,
    CollectionNoteCreateUpdateSerializer,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "serializer",
    [
        (CollectionCourtDecisionCreateUpdateSerializer),
        (CollectionNoteCreateUpdateSerializer),
    ],
)
def test_validate_debt_collection_superuser_allowed(
    lease_with_generated_service_unit_factory,
    user_factory,
    serializer,
):
    """
    Debt collection serializers should allow a superuser to pass service unit validation for any lease.
    """
    superuser = user_factory(is_superuser=True)
    request = MagicMock()
    request.user = superuser
    serializer = serializer(context={"request": request})

    data = {"lease": lease_with_generated_service_unit_factory()}
    assert serializer.validate(data) == data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_has_correct_service_unit,serializer",
    [
        (False, CollectionCourtDecisionCreateUpdateSerializer),
        (True, CollectionCourtDecisionCreateUpdateSerializer),
        (True, CollectionNoteCreateUpdateSerializer),
        (False, CollectionNoteCreateUpdateSerializer),
    ],
)
def test_validate_debt_collection_service_unit_access(
    lease_test_data,
    service_unit_factory,
    user_factory,
    user_has_correct_service_unit,
    serializer,
):
    """
    Debt collection serializers should allow a normal users to create and update data
    only when the user belongs to the same service unit as the lease.
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
    serializer = serializer(context={"request": request})
    data = {"lease": lease}

    if user_has_correct_service_unit:
        assert serializer.validate(data) == data
    else:
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "num_invoices,collection_stage,should_be_valid",
    [
        # Payment deferral requires exactly one invoice
        (0, CollectionStage.PAYMENT_DEFERRAL, False),
        (1, CollectionStage.PAYMENT_DEFERRAL, True),
        (2, CollectionStage.PAYMENT_DEFERRAL, False),
        # Notice has no invoice requirement
        (0, CollectionStage.NOTICE, True),
        (2, CollectionStage.NOTICE, True),
        # Empty stage should pass the validation entirely
        (0, None, True),
        (2, None, True),
        # All other stages require at least one invoice
        *[
            (num_invoices, stage, num_invoices > 0)
            for stage in CollectionStage
            if stage not in (CollectionStage.PAYMENT_DEFERRAL, CollectionStage.NOTICE)
            for num_invoices in (0, 2)
        ],
    ],
)
def test_collection_note_invoices_field(
    lease_test_data,
    user_factory,
    invoice_factory,
    num_invoices,
    collection_stage,
    should_be_valid,
):
    """
    Test the invoices field validation for different collection stages.
    Payment deferral collection should only accept one invoice.
    Notice should have no requirements. Other stages require at least one invoice.
    """
    lease = lease_test_data["lease"]
    user = user_factory(service_units=[lease.service_unit])
    request = MagicMock()
    request.user = user
    serializer = CollectionNoteCreateUpdateSerializer(context={"request": request})

    invoices = [
        invoice_factory(
            lease=lease,
            total_amount=Decimal("123.45"),
            billed_amount=Decimal("123.45"),
            outstanding_amount=Decimal("123.45"),
        )
        for _ in range(num_invoices)
    ]

    data = {
        "lease": lease,
        "collection_stage": collection_stage,
        "user": user,
        "postpone_date": (
            datetime.date(2026, 1, 1)
            if collection_stage == CollectionStage.PAYMENT_DEFERRAL
            else None
        ),
        "invoices": invoices,
    }

    if should_be_valid:
        assert serializer.validate(data) == data
    else:
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "collection_stage,postpone_date,should_be_valid",
    [
        (CollectionStage.PAYMENT_DEFERRAL, datetime.date(2026, 1, 1), True),
        (CollectionStage.PAYMENT_DEFERRAL, None, False),
        # All other stages should fail when postpone_date is present
        *[
            (stage, postpone_date, postpone_date is None)
            for stage in CollectionStage
            if stage != CollectionStage.PAYMENT_DEFERRAL
            for postpone_date in (datetime.date(2026, 1, 1), None)
        ],
    ],
)
def test_collection_note_postpone_date_validation(
    lease_test_data,
    user_factory,
    invoice_factory,
    collection_stage,
    postpone_date,
    should_be_valid,
):
    """
    Postpone date should be required for payment deferral, and not allowed for other stages
    """
    lease = lease_test_data["lease"]
    user = user_factory(service_units=[lease.service_unit])
    request = MagicMock()
    request.user = user
    serializer = CollectionNoteCreateUpdateSerializer(context={"request": request})

    data = {
        "lease": lease,
        "collection_stage": collection_stage,
        "user": user,
        "postpone_date": postpone_date,
        "invoices": [
            invoice_factory(
                lease=lease,
                total_amount=Decimal("123.45"),
                billed_amount=Decimal("123.45"),
                outstanding_amount=Decimal("123.45"),
            )
        ],
    }

    if should_be_valid:
        assert serializer.validate(data) == data
    else:
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
def test_payment_deferral_sets_postpone_date_on_invoice(
    lease_test_data,
    user_factory,
    invoice_factory,
):
    """
    Payment deferral should update selected invoice's postpone date.
    """
    lease = lease_test_data["lease"]
    user = user_factory(service_units=[lease.service_unit])
    request = MagicMock()
    request.user = user
    serializer = CollectionNoteCreateUpdateSerializer(context={"request": request})

    invoice = invoice_factory(
        lease=lease,
        total_amount=Decimal("123.45"),
        billed_amount=Decimal("123.45"),
        outstanding_amount=Decimal("123.45"),
    )

    invoice_postpone_date = datetime.date(2026, 1, 1)

    data = {
        "lease": lease,
        "collection_stage": CollectionStage.PAYMENT_DEFERRAL,
        "user": user,
        "postpone_date": invoice_postpone_date,
        "invoices": [invoice],
    }
    validated_data = serializer.validate(data)
    assert validated_data["postpone_date"] == invoice_postpone_date

    serializer.create(validated_data)
    invoice.refresh_from_db()
    assert invoice.postpone_date == invoice_postpone_date


@pytest.mark.django_db
@pytest.mark.parametrize(
    "collection_stage,entire_lease,inspection_date,should_be_valid",
    [
        (CollectionStage.CONTRACT_CHANGE, True, datetime.date(2026, 1, 1), True),
        (CollectionStage.CONTRACT_CHANGE, None, None, True),
        # All other stages should fail when either value is set
        *[
            (
                stage,
                entire_lease,
                inspection_date,
                entire_lease is False and inspection_date is None,
            )
            for stage in CollectionStage
            if stage != CollectionStage.CONTRACT_CHANGE
            for entire_lease in (True, False)
            for inspection_date in (datetime.date(2026, 1, 1), None)
        ],
    ],
)
def test_collection_note_entire_lease_and_inspection_date_validation(
    lease_test_data,
    user_factory,
    invoice_factory,
    collection_stage,
    entire_lease,
    inspection_date,
    should_be_valid,
):
    """
    Entire lease and inspection date should only be allowed for contract change.
    """
    lease = lease_test_data["lease"]
    user = user_factory(service_units=[lease.service_unit])
    request = MagicMock()
    request.user = user
    serializer = CollectionNoteCreateUpdateSerializer(context={"request": request})

    data = {
        "lease": lease,
        "collection_stage": collection_stage,
        "user": user,
        "entire_lease": entire_lease,
        "inspection_date": inspection_date,
        "postpone_date": (
            datetime.date(2026, 1, 1)
            if collection_stage == CollectionStage.PAYMENT_DEFERRAL
            else None
        ),
        "invoices": [
            invoice_factory(
                lease=lease,
                total_amount=Decimal("123.45"),
                billed_amount=Decimal("123.45"),
                outstanding_amount=Decimal("123.45"),
            )
        ],
    }

    if should_be_valid:
        assert serializer.validate(data) == data
    else:
        with pytest.raises(ValidationError):
            serializer.validate(data)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "collection_stage,should_create_decision",
    [
        (
            stage,
            stage
            in {
                CollectionStage.RISK_OF_DEMOLITION,
                CollectionStage.RISK_OF_DEMOLITION_AND_LITIGATION,
                CollectionStage.RISK_OF_LITIGATION,
                CollectionStage.RISK_OF_TERMINATION_AND_LITIGATION,
                CollectionStage.SIMPLE_PAYMENT_REMINDER,
            },
        )
        for stage in CollectionStage
    ],
)
def test_create_decision_on_collection_note_creation(
    lease_test_data,
    user_factory,
    invoice_factory,
    collection_stage,
    should_create_decision,
):
    """
    Collection notes with stages in STAGES_CREATING_DECISION should create a decision upon creation
    with a type, decision maker, date, and description. Other types should not create a decision.
    """
    lease = lease_test_data["lease"]
    user = user_factory(service_units=[lease.service_unit])
    request = MagicMock()
    request.user = user
    serializer = CollectionNoteCreateUpdateSerializer(context={"request": request})

    collection_note_sent_date = datetime.date(2026, 1, 1)
    collection_note_note = "text"

    data = {
        "lease": lease,
        "collection_stage": collection_stage,
        "user": user,
        "note": collection_note_note,
        "sent_date": collection_note_sent_date,
        "postpone_date": (
            datetime.date(2026, 1, 1)
            if collection_stage == CollectionStage.PAYMENT_DEFERRAL
            else None
        ),
        "invoices": [
            invoice_factory(
                lease=lease,
                total_amount=Decimal("123.45"),
                billed_amount=Decimal("123.45"),
                outstanding_amount=Decimal("123.45"),
            )
        ],
    }

    validated_data = serializer.validate(data)
    serializer.create(validated_data)

    decisions = Decision.objects.filter(lease=lease)
    decision = decisions.first()
    if should_create_decision:
        assert decisions.count() == 1
        assert decision is not None
        assert decision.decision_date == collection_note_sent_date
        assert decision.description == collection_note_note
        assert decision.type is not None
        assert decision.decision_maker is not None
    else:
        assert decisions.count() == 0
