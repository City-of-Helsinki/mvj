import pytest
from django.core.exceptions import ValidationError

from leasing.enums import ContactType


@pytest.mark.django_db
def test_contact_business_id_validator(contact_factory):
    with pytest.raises(ValidationError) as e:
        contact = contact_factory(type=ContactType.BUSINESS, business_id="1234567")
        contact.clean_fields()
    assert "business_id" in e.value.message_dict

    with pytest.raises(ValidationError) as e:
        contact = contact_factory(type=ContactType.BUSINESS, business_id="1234567-89")
        contact.clean_fields()
    assert "business_id" in e.value.message_dict
