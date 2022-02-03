import pytest
from faker import Faker
from rest_framework.exceptions import ValidationError

from ..serializers.form import AnswerSerializer, FormSerializer

fake = Faker("fi_FI")


def find(key, dictionary):
    for k, v in dictionary.iteritems():
        if k == key:
            yield v
        elif isinstance(v, dict):
            for result in find(key, v):
                yield result
        elif isinstance(v, list):
            for d in v:
                for result in find(key, d):
                    yield result


@pytest.mark.django_db
def test_form_serializer(basic_template_form):
    serializer = FormSerializer(basic_template_form, read_only=True)
    assert serializer.data["sections"]
    assert find("fields", serializer.data)
    assert find("choices", serializer.data)


@pytest.mark.django_db
def test_answer_serializer(basic_answer):
    serializer = AnswerSerializer(basic_answer)
    assert serializer.data["form"]
    assert serializer.data["entries"]


@pytest.mark.django_db
def test_entry_unique_validators(basic_answer, entry_factory):
    field = basic_answer.entries.first().field
    value = basic_answer.entries.first().value
    entry = entry_factory(answer=None, field=field, value=value)

    not_unique_entry = {
        "answer": None,
        "field": entry.field_id,
        "value": entry.value,
    }

    # check that validator does not accept non-unique entries
    with pytest.raises(ValidationError) as val_error:
        serializer = EntrySerializer(data=not_unique_entry)
        serializer.is_valid(True)
    assert hasattr(val_error, "value")
    assert val_error.value.args[0]["non_field_errors"][0].code == "unique"


@pytest.mark.django_db
def test_all_required_fields_answered_validator(
    basic_template_form_with_required_fields, admin_user
):

    entries = {}
    # Generating answers where required fields are not given
    for section in basic_template_form_with_required_fields.sections.all():
        entries[section.identifier] = dict()
        for field in section.fields.all():
            if field.section.identifier == "person-information":
                continue
            entries[section.identifier][field.identifier] = fake.name()

    answer_data = {
        "form": basic_template_form_with_required_fields.id,
        "user": admin_user.id,
        "entries": entries,
    }

    with pytest.raises(ValidationError) as val_error:
        answer_serializer = AnswerSerializer(data=answer_data)
        answer_serializer.is_valid(True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "required"


@pytest.mark.django_db
def test_social_security_validator(basic_template_form, admin_user):

    social_security_field = None
    for section in basic_template_form.sections.all():
        for field in section.fields.all():
            if field.identifier == "henkilotunnus":
                social_security_field = field
    entries = dict(dict())
    entries[social_security_field.section.identifier] = dict()
    entries[social_security_field.section.identifier][social_security_field.identifier] = "010181-900C"

    answer_data = {
        "form": basic_template_form.id,
        "user": admin_user.id,
        "entries": entries,
    }

    answer_serializer = AnswerSerializer(data=answer_data)
    # test that a correctly formatted ssn passes the validator
    assert answer_serializer.is_valid()

    answer_data["entries"][social_security_field.section.identifier][social_security_field.identifier] = "010181B900C"
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "invalid_ssn"


@pytest.mark.django_db
def test_company_id_validator(basic_template_form, admin_user):

    company_id_field = None
    for section in basic_template_form.sections.all():
        for field in section.fields.all():
            if field.identifier == "y-tunnus":
                company_id_field = field

    entries = dict(dict())
    entries[company_id_field.section.identifier] = dict()
    entries[company_id_field.section.identifier][company_id_field.identifier] = "1234567-8"

    answer_data = {
        "form": basic_template_form.id,
        "user": admin_user.id,
        "entries": entries,
    }

    answer_serializer = AnswerSerializer(data=answer_data)
    # test that a correctly formatted ssn passes the validator
    assert answer_serializer.is_valid()

    answer_data["entries"][company_id_field.section.identifier][company_id_field.identifier] = "12345A7-8"
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "invalid_company_id"
