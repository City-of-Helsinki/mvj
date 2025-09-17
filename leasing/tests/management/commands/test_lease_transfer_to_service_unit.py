import datetime
from typing import TypeAlias

import pytest
from auditlog.models import LogEntry
from django.core.management.base import CommandError
from django.db.models import QuerySet

from conftest import ContactFactory, TenantFactory
from leasing.enums import ContactType, DecisionTypeKind, TenantContactType
from leasing.management.commands.transfer_lease_to_service_unit import (
    COLLATERAL_NOTE_SERVICE_UNIT_TRANSFER,
    Command,
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


@pytest.fixture
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

    target_service_unit: ServiceUnit = service_unit_factory()
    target_lessor: Contact = contact_factory(
        type=ContactType.UNIT, service_unit=target_service_unit
    )
    target_receivable_type: ReceivableType = receivable_type_factory(
        service_unit=target_service_unit
    )
    target_intended_use: IntendedUse = intended_use_factory(
        service_unit=target_service_unit
    )
    transferrer_user = user_factory(email="transferrer@localhost")

    decision_reference_number = "HEL 2025-001122"
    decision_maker = decision_maker_factory()
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
def test_perform_single_transfer(single_lease_transfer_setup, command_instance):
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

    for collateral in collaterals:
        assert COLLATERAL_NOTE_SERVICE_UNIT_TRANSFER in collateral.note
        collateral_log_entry = LogEntry.objects.get_for_object(collateral).first()
        assert collateral_log_entry.action == LogEntry.Action.UPDATE
        collateral_changes = collateral_log_entry.changes
        assert [
            COLLATERAL_NOTES_INITIAL,
            f"{COLLATERAL_NOTES_INITIAL} - {COLLATERAL_NOTE_SERVICE_UNIT_TRANSFER}",
        ] == collateral_changes["note"]

    latest_comment: Comment = lease.comments.last()
    assert latest_comment.user == transferrer_user
    assert latest_comment.lease == lease
    latest_comment_text: str = latest_comment.text
    assert latest_comment_text.startswith("Vuokraus on siirretty")
    assert latest_comment_text.endswith(f"{target_service_unit}.")

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
        None,
        f"Vuokraus siirretty palveluyksiköstä {source_service_unit} → {target_service_unit}",
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
    assert "Must provide" in str(exc.value)


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
    assert "must be 'decision_maker_name', but found 'decision_date'" in str(exc.value)


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
    assert "Must provide" in str(exc.value)
