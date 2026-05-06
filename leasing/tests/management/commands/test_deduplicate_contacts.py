from datetime import timezone as dt_timezone
from typing import Callable
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils import timezone

from leasing.enums import ContactType
from leasing.models.contact import Contact
from leasing.models.service_unit import ServiceUnit

TARGET_DATE = "2025-11-27"


def _create_contact(
    contact_factory: Callable[..., Contact], service_unit: ServiceUnit, **kwargs
):
    """Create a contact with created_at forced to TARGET_DATE so the command picks it up."""
    contact = contact_factory(service_unit=service_unit, **kwargs)
    Contact.all_objects.filter(pk=contact.pk).update(
        created_at=timezone.datetime(2025, 11, 27, 12, 0, 0, tzinfo=dt_timezone.utc)
    )
    return contact


def _call(service_unit, tmp_path, **kwargs):
    """Call the command with the service unit and date patched to match test data."""
    with patch(
        "leasing.management.commands.deduplicate_contacts.Command.TARGET_SERVICE_UNIT_ID",
        service_unit.pk,
    ), patch(
        "leasing.management.commands.deduplicate_contacts.Command.TARGET_DATE",
        TARGET_DATE,
    ):
        call_command(
            "deduplicate_contacts",
            output=str(tmp_path / "report.json"),
            invoice_output=str(tmp_path / "invoices.json"),
            **kwargs,
        )


@pytest.mark.django_db
def test_duplicates_are_removed(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """The default happy path for deduplication."""
    service_unit = service_unit_factory()
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )

    _call(service_unit, tmp_path, replace_references=True, delete_duplicates=True)

    assert Contact.all_objects.filter(service_unit=service_unit).count() == 1


@pytest.mark.django_db
def test_oldest_contact_is_kept(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """The contact with the lowest pk (oldest) survives deduplication."""
    service_unit = service_unit_factory()
    original = _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )

    _call(service_unit, tmp_path, replace_references=True, delete_duplicates=True)

    surviving = Contact.all_objects.get(service_unit=service_unit)
    assert surviving.pk == original.pk


@pytest.mark.django_db
def test_contacts_with_different_name_are_not_deduplicated(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """Contacts sharing only business_id but with different names are kept separate."""
    service_unit = service_unit_factory()
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp (old)",
        business_id="1234567-8",
    )

    _call(service_unit, tmp_path, replace_references=True, delete_duplicates=True)

    assert Contact.all_objects.filter(service_unit=service_unit).count() == 2


@pytest.mark.django_db
def test_contacts_with_different_business_id_are_not_deduplicated(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """Contacts sharing only name but with different business_ids are kept separate."""
    service_unit = service_unit_factory()
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="9999999-9",
    )

    _call(service_unit, tmp_path, replace_references=True, delete_duplicates=True)

    assert Contact.all_objects.filter(service_unit=service_unit).count() == 2


@pytest.mark.django_db
def test_dry_run_does_not_remove_contacts(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """Without --replace-references the command is read-only and removes nothing."""
    service_unit = service_unit_factory()
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )
    _create_contact(
        contact_factory,
        service_unit,
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
    )

    _call(service_unit, tmp_path)

    assert Contact.all_objects.filter(service_unit=service_unit).count() == 2


@pytest.mark.django_db
def test_contacts_outside_target_date_are_not_affected(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """Contacts created on a date other than TARGET_DATE are not considered duplicates."""
    service_unit = service_unit_factory()
    # Created at the default (now), not TARGET_DATE
    contact_factory(
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
        service_unit=service_unit,
    )
    contact_factory(
        type=ContactType.BUSINESS,
        name="Acme Corp",
        business_id="1234567-8",
        service_unit=service_unit,
    )

    _call(service_unit, tmp_path, replace_references=True, delete_duplicates=True)

    assert Contact.all_objects.filter(service_unit=service_unit).count() == 2


@pytest.mark.django_db
def test_contacts_outside_service_unit_are_not_affected(
    service_unit_factory: Callable[..., ServiceUnit],
    contact_factory: Callable[..., Contact],
    tmp_path,
):
    """Duplicates in a different service unit are not touched."""
    target_unit = service_unit_factory()
    other_unit = service_unit_factory()

    for _ in range(2):
        _create_contact(
            contact_factory,
            other_unit,
            type=ContactType.BUSINESS,
            name="Acme Corp",
            business_id="1234567-8",
        )

    _call(target_unit, tmp_path, replace_references=True, delete_duplicates=True)

    assert Contact.all_objects.filter(service_unit=other_unit).count() == 2
