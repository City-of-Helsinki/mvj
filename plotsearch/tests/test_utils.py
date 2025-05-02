import pytest

from leasing.models.contact import Contact
from leasing.models.service_unit import ServiceUnit
from plotsearch.enums import AreaSearchLessor
from plotsearch.utils import (
    _get_lessor_email_to_address,
    map_intended_use_to_service_unit_id,
    map_lessor_enum_to_service_unit_id,
)


@pytest.mark.parametrize(
    "intended_use_name,lessor",
    [
        ("Ravitsemus, myynti ja mainonta", "AKV"),
        ("Taide ja kulttuuri", "AKV"),
        ("Varastointi ja jakelu", "AKV"),
        ("Työmaat", "AKV"),
        ("Muu alueen käyttö", "MAKE"),
        ("Veneily ja laiturit", "UPA"),
        ("Urheilu ja Liikunta", "LIPA"),
    ],
)
@pytest.mark.django_db
def test_map_intended_use_to_service_unit_id(
    intended_use_name,
    lessor,
    setup_lessor_contacts_and_service_units,
    area_search_intended_use_factory,
):
    """Test that the intended use maps to the correct service unit ID."""

    intended_use = area_search_intended_use_factory(
        name=intended_use_name, name_fi=intended_use_name
    )
    assert map_intended_use_to_service_unit_id(
        intended_use
    ) == map_lessor_enum_to_service_unit_id(lessor)


@pytest.mark.django_db
def test_get_lessor_email_address(
    setup_lessor_contacts_and_service_units, contact_factory
):
    """
    Test that the lessor email address is retrieved correctly.
    """
    # Correct cases where contact and email address exist exactly once
    for lessor in AreaSearchLessor:
        unit_id = map_lessor_enum_to_service_unit_id(lessor)
        contact = Contact.objects.get(service_unit_id=unit_id, is_lessor=True)
        email_address = _get_lessor_email_to_address(lessor)
        assert email_address == contact.email

    # Case where contact does not exist
    lessor_no_contact = AreaSearchLessor.MAKE
    unit_id = map_lessor_enum_to_service_unit_id(lessor_no_contact)
    Contact.objects.get(service_unit_id=unit_id, is_lessor=True).delete()
    with pytest.raises(ValueError):
        _get_lessor_email_to_address(lessor_no_contact)

    # Case where contact exists but email address doesn't
    lessor_no_email = AreaSearchLessor.AKV
    unit_id = map_lessor_enum_to_service_unit_id(lessor_no_email)
    contact = Contact.objects.get(service_unit_id=unit_id, is_lessor=True)
    contact.email = None
    contact.save()
    with pytest.raises(ValueError):
        _get_lessor_email_to_address(lessor_no_email)

    # Case where multiple contacts with same criteria exists
    duplicate_lessor = AreaSearchLessor.LIPA
    unit_id = map_lessor_enum_to_service_unit_id(duplicate_lessor)
    service_unit = ServiceUnit.objects.get(pk=unit_id)
    for i in range(2):
        contact_factory(
            name="anything",
            service_unit=service_unit,
            is_lessor=True,
            email="anything@example.com",
        )
    with pytest.raises(ValueError):
        _get_lessor_email_to_address(duplicate_lessor)
