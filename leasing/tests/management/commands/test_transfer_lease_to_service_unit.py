import datetime
from typing import TypeAlias
from unittest.mock import patch

import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.core.management.base import CommandError
from django.db.models import QuerySet
from django.utils import timezone

from conftest import ContactFactory, TenantFactory
from leasing.enums import ContactType, DecisionTypeKind, TenantContactType
from leasing.management.commands.transfer_lease_to_service_unit import (
    Command,
    TransferRow,
)
from leasing.models.comment import Comment
from leasing.models.contact import Contact
from leasing.models.contract import Collateral, Contract
from leasing.models.decision import Decision, DecisionMaker
from leasing.models.lease import IntendedUse, Lease
from leasing.models.receivable_type import ReceivableType
from leasing.models.rent import Rent
from leasing.models.service_unit import ServiceUnit
from users.models import User

OldValue: TypeAlias = str
NewValue: TypeAlias = str

COLLATERAL_NOTES_INITIAL = "Initial collateral notes."


@pytest.fixture
def command_instance():
    return Command()


@pytest.fixture(scope="function")
def single_lease_transfer_setup(
    lease_factory,
    contact_factory: ContactFactory,
    tenant_factory: TenantFactory,
    tenant_contact_factory,
    receivable_type_factory,
    intended_use_factory,
    rent_factory,
    contract_factory,
    collateral_factory,
    service_unit_factory,
    user_factory,
    decision_maker_factory,
) -> tuple[
    Lease,
    ServiceUnit,
    Contact,
    ReceivableType,
    IntendedUse,
    User,
    str,
    DecisionMaker,
    str,
    str,
]:
    # Django fixture loading in `leasing/tests/conftest.py:django_db_setup` is messing up django-auditlog
    # The only way to recover for this test I found is registering the models again.
    models = [Lease, Contact, Rent, Collateral, Decision]
    for model in models:
        if not auditlog.contains(model):
            auditlog.register(model)

    source_service_unit: ServiceUnit = service_unit_factory()
    source_lessor: Contact = contact_factory(
        type=ContactType.UNIT, service_unit=source_service_unit
    )
    source_receivable_type: ReceivableType = receivable_type_factory(
        service_unit=source_service_unit,
    )
    source_intended_use: IntendedUse = intended_use_factory(
        service_unit=source_service_unit
    )
    lease: Lease = lease_factory(
        service_unit=source_service_unit,
        lessor=source_lessor,
        intended_use=source_intended_use,
        end_date=datetime.date(2030, 12, 31),
    )
    rent_factory(
        lease=lease,
        override_receivable_type=source_receivable_type,
    )
    contract: Contract = contract_factory(lease=lease)
    collateral_factory(contract=contract, note=COLLATERAL_NOTES_INITIAL)
    contact_1, contact_2 = contact_factory.create_batch(
        2, type=ContactType.PERSON, service_unit=source_service_unit
    )
    tenant_1, tenant_2 = tenant_factory.create_batch(
        2, lease=lease, share_numerator=1, share_denominator=2
    )
    tenant_contact_factory(
        tenant=tenant_1,
        contact=contact_1,
        type=TenantContactType.TENANT,
        start_date=datetime.date(2025, 1, 1),
    )
    tenant_contact_factory(
        tenant=tenant_2,
        contact=contact_2,
        type=TenantContactType.TENANT,
        start_date=datetime.date(2025, 1, 1),
    )

    target_service_unit: ServiceUnit = service_unit_factory(name="Target Service Unit")
    target_lessor: Contact = contact_factory(
        name="Target Lessor",
        type=ContactType.UNIT,
        service_unit=target_service_unit,
        is_lessor=True,
    )
    target_receivable_type: ReceivableType = receivable_type_factory(
        name="Target Receivable Type", service_unit=target_service_unit
    )
    target_intended_use: IntendedUse = intended_use_factory(
        name="Target Intended Use", service_unit=target_service_unit
    )
    transferrer_user = user_factory(email="transferrer@localhost")

    decision_reference_number = "HEL 2025-001122"
    decision_maker = decision_maker_factory(name="Decision Maker")
    decision_date = "2025-09-30"
    decision_section = "0123"

    return (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        transferrer_user,
        decision_reference_number,
        decision_maker,
        decision_date,
        decision_section,
    )


@pytest.mark.django_db
def test_perform_single_transfer(
    single_lease_transfer_setup, command_instance: Command
):
    mock_now = timezone.datetime(2025, 9, 30, 9, 30, 0, tzinfo=datetime.timezone.utc)
    (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        transferrer_user,
        decision_reference_number,
        decision_maker,
        decision_date,
        decision_section,
    ) = single_lease_transfer_setup
    source_service_unit = lease.service_unit
    source_lessor = lease.lessor
    source_intended_use = lease.intended_use
    source_receivable_type = lease.rents.first().override_receivable_type

    with patch("django.utils.timezone.now", return_value=mock_now):
        command_instance.perform_single_transfer(
            lease,
            target_service_unit,
            target_lessor,
            target_receivable_type,
            target_intended_use,
            transferrer_user,
            decision_reference_number,
            decision_maker,
            decision_date,
            decision_section,
        )
    lease: Lease
    lease.refresh_from_db()
    assert lease.service_unit == target_service_unit
    assert lease.lessor == target_lessor
    assert lease.intended_use == target_intended_use

    lease_log_entries = LogEntry.objects.get_for_object(lease)
    assert (
        lease_log_entries.count() == 3
    ), "There should be three log entries for the lease."
    lease_log_entry = lease_log_entries[
        1
    ]  # Second entry is correct, first entry should be custom LogEntry

    lease_changes: dict[str, tuple[OldValue, NewValue]] = (
        lease_log_entry.changes
    )  # Typed as tuple but is list with the tuples shape

    assert [str(source_service_unit.id), str(target_service_unit.id)] == lease_changes[
        "service_unit"
    ]
    assert [str(source_lessor.id), str(target_lessor.id)] == lease_changes["lessor"]
    assert [str(source_intended_use.id), str(target_intended_use.id)] == lease_changes[
        "intended_use"
    ]

    for tenant in lease.tenants.all():
        for contact in tenant.contacts.all():
            assert contact.service_unit == target_service_unit
            contact_log_entries = LogEntry.objects.get_for_object(contact)
            assert len(contact_log_entries) == 1
            assert contact_log_entries[0].action == LogEntry.Action.CREATE

    rents: QuerySet[Rent] = lease.rents.all()
    assert rents.count() == 1, "There should be one rent associated with the lease."

    for rent in rents:
        assert rent.override_receivable_type == target_receivable_type

        rent_log_entries = LogEntry.objects.get_for_object(rent)
        assert len(rent_log_entries) == 2  # One for creation, one for update
        rent_log_entry = rent_log_entries.first()
        assert rent_log_entry.action == LogEntry.Action.UPDATE
        rent_changes = rent_log_entry.changes
        assert [
            str(source_receivable_type.id),
            str(target_receivable_type.id),
        ] == rent_changes["override_receivable_type"]

    contracts: QuerySet[Contract] = lease.contracts.all()
    assert (
        contracts.count() == 1
    ), "There should be one contract associated with the lease."

    collaterals: QuerySet[Collateral] = contracts.first().collaterals.all()
    assert (
        collaterals.count() == 1
    ), "There should be one collateral associated with the contract."

    transfer_note = command_instance.get_service_unit_transfer_note(
        target_service_unit, source_service_unit, mock_now
    )
    for collateral in collaterals:
        assert (
            command_instance.get_service_unit_transfer_note(
                target_service_unit, source_service_unit, mock_now
            )
            in collateral.note
        )
        collateral_log_entry = LogEntry.objects.get_for_object(collateral).first()
        assert collateral_log_entry.action == LogEntry.Action.UPDATE
        collateral_changes = collateral_log_entry.changes
        assert [
            COLLATERAL_NOTES_INITIAL,
            f"{COLLATERAL_NOTES_INITIAL} - {transfer_note}",
        ] == collateral_changes["note"]

    latest_comment: Comment = lease.comments.last()
    assert latest_comment.user == transferrer_user
    assert latest_comment.lease == lease
    latest_comment_text: str = latest_comment.text
    assert latest_comment_text == transfer_note

    decision: Decision = lease.decisions.last()
    assert decision.lease == lease
    assert decision.type.kind == DecisionTypeKind.LEASE_SERVICE_UNIT_TRANSFER

    decision_log_entry = LogEntry.objects.get_for_object(decision).first()
    assert decision_log_entry.action == LogEntry.Action.CREATE
    decision_changes = decision_log_entry.changes
    assert [str(None), str(lease.id)] == decision_changes["lease"]
    assert [str(None), decision_reference_number] == decision_changes[
        "reference_number"
    ]
    assert [str(None), str(decision_maker.id)] == decision_changes["decision_maker"]
    assert [str(None), decision_date] == decision_changes["decision_date"]
    assert [str(None), decision_section] == decision_changes["section"]

    lease_custom_log_entry = LogEntry.objects.get_for_object(lease).first()
    assert lease_custom_log_entry.action == LogEntry.Action.UPDATE
    assert [
        "None",
        command_instance.get_service_unit_transfer_note(
            target_service_unit, source_service_unit, mock_now
        ),
    ] == lease_custom_log_entry.changes["service_unit_transfer"]


def test_validate_headers_correct(command_instance):
    headers = [
        "lease_identifier",
        "target_service_unit_name",
        "target_lessor_name",
        "target_receivable_type_name",
        "target_intended_use_name",
        "transferrer_email",
        "decision_reference_number",
        "decision_maker_name",
        "decision_date",
        "decision_section",
    ]
    # Should not raise
    command_instance.validate_headers(headers)


def test_validate_headers_wrong_length(command_instance):
    headers = [
        "lease_identifier",
        "target_service_unit_name",
        "target_lessor_name",
        "target_receivable_type_name",
        "target_intended_use_name",
        "transferrer_email",
        "decision_reference_number",
        "decision_maker_name",
        "decision_date",
        # Missing "decision_section"
    ]
    with pytest.raises(CommandError) as exc:
        command_instance.validate_headers(headers)
    assert "Invalid CSV headers" in str(exc.value)


def test_validate_headers_wrong_order(command_instance):
    headers = [
        "lease_identifier",
        "target_service_unit_name",
        "target_lessor_name",
        "target_receivable_type_name",
        "target_intended_use_name",
        "transferrer_email",
        "decision_reference_number",
        "decision_date",  # Should be "decision_maker_name"
        "decision_maker_name",  # Should be "decision_date"
        "decision_section",
    ]
    with pytest.raises(CommandError) as exc:
        command_instance.validate_headers(headers)
    assert "Invalid CSV headers, found 2 errors!" in str(exc.value)


def test_validate_headers_extra_column(command_instance):
    headers = [
        "lease_identifier",
        "target_service_unit_name",
        "target_lessor_name",
        "target_receivable_type_name",
        "target_intended_use_name",
        "transferrer_email",
        "decision_reference_number",
        "decision_maker_name",
        "decision_date",
        "decision_section",
        "extra_column",
    ]
    with pytest.raises(CommandError) as exc:
        command_instance.validate_headers(headers)
    assert "Invalid CSV headers, found 1 errors!" in str(exc.value)


@pytest.mark.django_db
def test_validate_target_objects_lease_end_date(
    single_lease_transfer_setup, command_instance: Command
):
    mock_now = timezone.datetime(2025, 9, 30, 9, 30, 0, tzinfo=datetime.timezone.utc)
    (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        _transferrer_user,
        _decision_reference_number,
        _decision_maker,
        _decision_date,
        _decision_section,
    ) = single_lease_transfer_setup

    # `end_date` in the future
    with patch("django.utils.timezone.now", return_value=mock_now):
        # Should not raise
        errors = command_instance.validate_target_objects(
            lease,
            target_service_unit,
            target_lessor,
            target_receivable_type,
            target_intended_use,
            0,
        )
    assert len(errors) == 0

    # `end_date` in the past
    lease.end_date = timezone.datetime(
        2025, 9, 29, 1, 59, 0, tzinfo=datetime.timezone.utc
    )
    lease.save()
    lease.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=mock_now):
        errors = command_instance.validate_target_objects(
            lease,
            target_service_unit,
            target_lessor,
            target_receivable_type,
            target_intended_use,
            0,
        )
    assert len(errors) == 1
    assert f"Lease {lease.identifier} has ended already!" in errors[0]

    # `end_date` not set
    lease.end_date = None
    lease.save()
    lease.refresh_from_db()

    with patch("django.utils.timezone.now", return_value=mock_now):
        # Should not raise
        errors = command_instance.validate_target_objects(
            lease,
            target_service_unit,
            target_lessor,
            target_receivable_type,
            target_intended_use,
            0,
        )
    assert len(errors) == 0


@pytest.mark.django_db
def test_perform_transfer_leases(
    single_lease_transfer_setup, command_instance: Command
):
    """Test the transfer_leases method with a complete CSV row transfer."""
    mock_now = timezone.datetime(2025, 9, 30, 9, 30, 0, tzinfo=datetime.timezone.utc)
    (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        transferrer_user,
        decision_reference_number,
        decision_maker,
        decision_date,
        decision_section,
    ) = single_lease_transfer_setup

    test_row: TransferRow = {
        "lease_identifier": lease.identifier.identifier,
        "target_service_unit_name": target_service_unit.name,
        "target_lessor_name": target_lessor.name,
        "target_receivable_type_name": target_receivable_type.name,
        "target_intended_use_name": target_intended_use.name,
        "transferrer_email": transferrer_user.email,
        "decision_reference_number": decision_reference_number,
        "decision_maker_name": decision_maker.name,
        "decision_date": decision_date,
        "decision_section": decision_section,
    }

    original_service_unit = lease.service_unit

    with patch("django.utils.timezone.now", return_value=mock_now):
        command_instance.perform_transfer_leases([test_row])

    # Lease was transferred
    lease.refresh_from_db()
    assert lease.service_unit == target_service_unit
    assert lease.lessor == target_lessor
    assert lease.intended_use == target_intended_use

    # Rents were updated
    for rent in lease.rents.all():
        assert rent.override_receivable_type == target_receivable_type

    # Contacts were copied to new service unit
    for tenant in lease.tenants.all():
        for contact in tenant.contacts.all():
            assert contact.service_unit == target_service_unit

    # Comment was added
    latest_comment = lease.comments.last()
    assert latest_comment.user == transferrer_user
    expected_note = command_instance.get_service_unit_transfer_note(
        target_service_unit, original_service_unit, mock_now
    )
    assert latest_comment.text == expected_note

    # Decision was created
    decision = lease.decisions.last()
    assert decision.reference_number == decision_reference_number
    assert decision.decision_maker == decision_maker
    assert decision.section == decision_section

    # Collateral notes were updated
    for contract in lease.contracts.all():
        for collateral in contract.collaterals.all():
            assert expected_note in collateral.note


@pytest.mark.django_db
def test_perform_transfer_leases_with_validation_error(
    single_lease_transfer_setup, command_instance: Command
):
    """Test that transfer_leases rolls back transaction on validation errors."""
    (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        transferrer_user,
        decision_reference_number,
        decision_maker,
        decision_date,
        decision_section,
    ) = single_lease_transfer_setup

    # Row with invalid lease identifier
    invalid_row: TransferRow = {
        "lease_identifier": "INVALID-LEASE-ID",
        "target_service_unit_name": target_service_unit.name,
        "target_lessor_name": target_lessor.name,
        "target_receivable_type_name": target_receivable_type.name,
        "target_intended_use_name": target_intended_use.name,
        "transferrer_email": transferrer_user.email,
        "decision_reference_number": decision_reference_number,
        "decision_maker_name": decision_maker.name,
        "decision_date": decision_date,
        "decision_section": decision_section,
    }

    original_service_unit = lease.service_unit
    original_comment_count = lease.comments.count()
    original_decision_count = lease.decisions.count()

    with pytest.raises(CommandError) as exc_info:
        command_instance.perform_transfer_leases([invalid_row])

    assert "Could not get target objects" in str(exc_info.value)

    # Verify transaction was rolled back
    lease.refresh_from_db()
    assert lease.service_unit == original_service_unit
    assert lease.comments.count() == original_comment_count
    assert lease.decisions.count() == original_decision_count


@pytest.mark.django_db
def test_perform_transfer_leases_exception_handling(
    single_lease_transfer_setup, command_instance: Command
):
    """Test that unexpected exceptions are wrapped in CommandError."""
    (
        lease,
        target_service_unit,
        target_lessor,
        target_receivable_type,
        target_intended_use,
        transferrer_user,
        decision_reference_number,
        decision_maker,
        decision_date,
        decision_section,
    ) = single_lease_transfer_setup

    test_row: TransferRow = {
        "lease_identifier": lease.identifier.identifier,
        "target_service_unit_name": target_service_unit.name,
        "target_lessor_name": target_lessor.name,
        "target_receivable_type_name": target_receivable_type.name,
        "target_intended_use_name": target_intended_use.name,
        "transferrer_email": transferrer_user.email,
        "decision_reference_number": decision_reference_number,
        "decision_maker_name": decision_maker.name,
        "decision_date": decision_date,
        "decision_section": decision_section,
    }

    # Mock perform_single_transfer to raise an unexpected exception
    with patch.object(
        command_instance,
        "perform_single_transfer",
        side_effect=ValueError("Unexpected error"),
    ):
        with pytest.raises(CommandError) as exc_info:
            command_instance.perform_transfer_leases([test_row])

        assert "Transfer failed: Unexpected error" in str(exc_info.value)

    # Verify transaction was rolled back
    lease.refresh_from_db()
    assert lease.service_unit != target_service_unit  # Should not have changed
