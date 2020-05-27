import pytest

from laske_export.document.sales_order import Party
from leasing.enums import ContactType


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_name, last_name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            None,
            # Expected
            "",
            None,
            None,
            None,
        ),
        (
            # Name
            "First",
            None,
            # Expected
            "First",
            None,
            None,
            None,
        ),
        (
            # Name
            None,
            "Last",
            # Expected
            "Last",
            None,
            None,
            None,
        ),
        (
            # Name
            "First name 1",
            "Last name 1",
            # Expected
            "First name 1 Last name 1",
            None,
            None,
            None,
        ),
        (
            # Name
            "Super long first name 123456789abcde",
            "Super long last name 123456789abcde",
            # Expected
            "Super long first name 123456789abcd",
            "e Super long last name 123456789abc",
            "de",
            None,
        ),
        (
            # Name
            "Super super super super hyper mega long first name 123456789abcdefghijklm",
            "Super super super super hyper mega long last name 123456789abcdefghijklmn",
            # Expected
            "Super super super super hyper mega ",
            "long first name 123456789abcdefghij",
            "klm Super super super super hyper m",
            "ega long last name 123456789abcdefg",
        ),
    ],
)
def test_party_from_contact_person_name(
    django_db_setup,
    contact_factory,
    first_name,
    last_name,
    expected1,
    expected2,
    expected3,
    expected4,
):
    contact = contact_factory(
        first_name=first_name, last_name=last_name, type=ContactType.PERSON
    )

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1
    assert party.priority_name2 == expected2
    assert party.priority_name3 == expected3
    assert party.priority_name4 == expected4
    assert party.info_name1 == expected1
    assert party.info_name2 == expected2
    assert party.info_name3 == expected3
    assert party.info_name4 == expected4


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_name, last_name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            None,
            # Expected
            "",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            "First",
            None,
            # Expected
            "First",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            None,
            "Last",
            # Expected
            "Last",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            "First name 1",
            "Last name 1",
            # Expected
            "First name 1 Last name 1",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            "Super long first name 123456789abcde",
            "Super long last name 123456789abcde",
            # Expected
            "Super long first name 123456789abcd",
            "e Super long last name 123456789abc",
            "de",
            "c/o Something random",
        ),
        (
            # Name
            "Super super super super hyper mega long first name 123456789abcdefghijklm",
            "Super super super super hyper mega long last name 123456789abcdefghijklmn",
            # Expected
            "Super super super super hyper mega ",
            "long first name 123456789abcdefghij",
            "klm Super super super super hyper m",
            "c/o Something random",
        ),
    ],
)
def test_party_from_contact_person_name_with_care_of(
    django_db_setup,
    contact_factory,
    first_name,
    last_name,
    expected1,
    expected2,
    expected3,
    expected4,
):
    contact = contact_factory(
        first_name=first_name,
        last_name=last_name,
        type=ContactType.PERSON,
        care_of="Something random",
    )

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1, "priority_name1"
    assert party.priority_name2 == expected2, "priority_name2"
    assert party.priority_name3 == expected3, "priority_name3"
    assert party.priority_name4 == expected4, "priority_name4"
    assert party.info_name1 == expected1, "info_name1"
    assert party.info_name2 == expected2, "info_name2"
    assert party.info_name3 == expected3, "info_name3"
    assert party.info_name4 == expected4, "info_name4"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_name, last_name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            None,
            # Expected
            "",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            "First",
            None,
            # Expected
            "First",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            None,
            "Last",
            # Expected
            "Last",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            "First name 1",
            "Last name 1",
            # Expected
            "First name 1 Last name 1",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            "Super long first name 123456789abcde",
            "Super long last name 123456789abcde",
            # Expected
            "Super long first name 123456789abcd",
            "e Super long last name 123456789abc",
            "de",
            "c/o Something random super long car",
        ),
        (
            # Name
            "Super super super super hyper mega long first name 123456789abcdefghijklm",
            "Super super super super hyper mega long last name 123456789abcdefghijklmn",
            # Expected
            "Super super super super hyper mega ",
            "long first name 123456789abcdefghij",
            "klm Super super super super hyper m",
            "c/o Something random super long car",
        ),
    ],
)
def test_party_from_contact_person_name_with_long_care_of(
    django_db_setup,
    contact_factory,
    first_name,
    last_name,
    expected1,
    expected2,
    expected3,
    expected4,
):
    contact = contact_factory(
        first_name=first_name,
        last_name=last_name,
        type=ContactType.PERSON,
        care_of="Something random super long care of name 123456789abcdefghijklmnopqrstuvwxyz"
        "zyxwvutsrqponmlkjihgfedcba987654321 eman fo erac gnol repus modnar gnihtemoS",
    )

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1, "priority_name1"
    assert party.priority_name2 == expected2, "priority_name2"
    assert party.priority_name3 == expected3, "priority_name3"
    assert party.priority_name4 == expected4, "priority_name4"
    assert party.info_name1 == expected1, "info_name1"
    assert party.info_name2 == expected2, "info_name2"
    assert party.info_name3 == expected3, "info_name3"
    assert party.info_name4 == expected4, "info_name4"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            # Expected
            "",
            None,
            None,
            None,
        ),
        (
            # Name
            "Business name",
            # Expected
            "Business name",
            None,
            None,
            None,
        ),
        (
            # Name
            "Super long business name 123456789abcde Super long business name 123456789abcde",
            # Expected
            "Super long business name 123456789a",
            "bcde Super long business name 12345",
            "6789abcde",
            None,
        ),
        (
            # Name
            "Super super super super hyper mega long business name 123456789abcdefghijklm"
            "Super super super super hyper mega long business name 123456789abcdefghijklm",
            # Expected
            "Super super super super hyper mega ",
            "long business name 123456789abcdefg",
            "hijklmSuper super super super hyper",
            " mega long business name 123456789a",
        ),
    ],
)
def test_party_from_contact_name(
    django_db_setup, contact_factory, name, expected1, expected2, expected3, expected4
):
    contact = contact_factory(name=name, type=ContactType.BUSINESS)

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1
    assert party.priority_name2 == expected2
    assert party.priority_name3 == expected3
    assert party.priority_name4 == expected4
    assert party.info_name1 == expected1
    assert party.info_name2 == expected2
    assert party.info_name3 == expected3
    assert party.info_name4 == expected4


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            # Expected
            "",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            "Business name",
            # Expected
            "Business name",
            "c/o Something random",
            None,
            None,
        ),
        (
            # Name
            "Super long business name 123456789abcde Super long business name 123456789abcde",
            # Expected
            "Super long business name 123456789a",
            "bcde Super long business name 12345",
            "6789abcde",
            "c/o Something random",
        ),
        (
            # Name
            "Super super super super hyper mega long business name 123456789abcdefghijklm"
            "Super super super super hyper mega long business name 123456789abcdefghijklm",
            # Expected
            "Super super super super hyper mega ",
            "long business name 123456789abcdefg",
            "hijklmSuper super super super hyper",
            "c/o Something random",
        ),
    ],
)
def test_party_from_contact_name_with_care_of(
    django_db_setup, contact_factory, name, expected1, expected2, expected3, expected4
):
    contact = contact_factory(
        name=name, type=ContactType.BUSINESS, care_of="Something random"
    )

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1, "priority_name1"
    assert party.priority_name2 == expected2, "priority_name2"
    assert party.priority_name3 == expected3, "priority_name3"
    assert party.priority_name4 == expected4, "priority_name4"
    assert party.info_name1 == expected1, "info_name1"
    assert party.info_name2 == expected2, "info_name2"
    assert party.info_name3 == expected3, "info_name3"
    assert party.info_name4 == expected4, "info_name4"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "name, expected1, expected2, expected3, expected4",
    [
        (
            # Name
            None,
            # Expected
            "",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            "Business name",
            # Expected
            "Business name",
            "c/o Something random super long car",
            "e of name 123456789abcdefghijklmnop",
            "qrstuvwxyzzyxwvutsrqponmlkjihgfedcb",
        ),
        (
            # Name
            "Super long business name 123456789abcde Super long business name 123456789abcde",
            # Expected
            "Super long business name 123456789a",
            "bcde Super long business name 12345",
            "6789abcde",
            "c/o Something random super long car",
        ),
        (
            # Name
            "Super super super super hyper mega long business name 123456789abcdefghijklm"
            "Super super super super hyper mega long businesst name 123456789abcdefghijklm",
            # Expected
            "Super super super super hyper mega ",
            "long business name 123456789abcdefg",
            "hijklmSuper super super super hyper",
            "c/o Something random super long car",
        ),
    ],
)
def test_party_from_contact_person_with_long_care_of(
    django_db_setup, contact_factory, name, expected1, expected2, expected3, expected4
):
    contact = contact_factory(
        name=name,
        type=ContactType.BUSINESS,
        care_of="Something random super long care of name 123456789abcdefghijklmnopqrstuvwxyz"
        "zyxwvutsrqponmlkjihgfedcba987654321 eman fo erac gnol repus modnar gnihtemoS",
    )

    party = Party()
    party.from_contact(contact)

    assert party.priority_name1 == expected1, "priority_name1"
    assert party.priority_name2 == expected2, "priority_name2"
    assert party.priority_name3 == expected3, "priority_name3"
    assert party.priority_name4 == expected4, "priority_name4"
    assert party.info_name1 == expected1, "info_name1"
    assert party.info_name2 == expected2, "info_name2"
    assert party.info_name3 == expected3, "info_name3"
    assert party.info_name4 == expected4, "info_name4"
