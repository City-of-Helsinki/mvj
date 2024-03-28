import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from faker import Faker
from rest_framework.exceptions import ValidationError

from plotsearch.enums import DeclineReason
from plotsearch.models import TargetStatus

from ..serializers.form import AnswerSerializer, FormSerializer, TargetStatusSerializer

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
    assert serializer.data["entries_data"]


"""
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
"""


def generate_entries(section, entries):
    entries["fields"] = dict()
    entries["sections"] = dict()
    for field in section.fields.all():
        entries["fields"][field.identifier] = {"value": fake.name(), "extraValue": ""}
    for subsection in section.subsections.all():
        entries["sections"][subsection.identifier] = dict()
        generate_entries(subsection, entries["sections"][subsection.identifier])


@pytest.mark.django_db
def test_all_required_fields_answered_validator(
    django_db_setup,
    basic_template_form_with_required_fields,
    plot_search_target,
    admin_user,
):

    entries = {}
    # Generating answers where required fields are not given
    for section in basic_template_form_with_required_fields.sections.filter(
        parent__isnull=True
    ):
        entries[section.identifier] = dict()
        generate_entries(section, entries[section.identifier])

    empty_section = basic_template_form_with_required_fields.sections.filter(
        parent__isnull=True
    )[1]

    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "hallintaosuus"
    ] = {"value": "1/1", "extraValue": ""}

    entries["hakijan-tiedot"]["sections"]["company-information"]["sections"][
        "contact-person"
    ]["fields"]["henkilotunnus"] = {
        "value": "010181-900C",
        "extraValue": "",
    }

    entries[empty_section.identifier]["sections"]["person-information"] = list()
    entries[empty_section.identifier]["sections"]["person-information"].append(
        {
            "fields": {
                "first-name-1": {"value": fake.name(), "extraValue": ""},
                "last-name-1": {"value": fake.name(), "extraValue": ""},
                "personal-identity-code-1": {"value": "", "extraValue": ""},
            }
        }
    )

    answer_data = {
        "form": basic_template_form_with_required_fields.id,
        "user": admin_user.id,
        "entries": entries,
        "targets": [plot_search_target.pk,],  # noqa: E231
    }

    with pytest.raises(ValidationError) as val_error:
        answer_serializer = AnswerSerializer(data=answer_data)
        answer_serializer.is_valid(raise_exception=True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "required"


@pytest.mark.django_db
def test_social_security_validator(
    django_db_setup, basic_template_form, plot_search_target, admin_user
):

    social_security_field = None
    for section in basic_template_form.sections.all():
        for field in section.fields.all():
            if field.identifier == "henkilotunnus":
                social_security_field = field
    entries = {}
    for section in basic_template_form.sections.filter(parent__isnull=True):
        entries[section.identifier] = dict()
        generate_entries(section, entries[section.identifier])
    entries["hakijan-tiedot"]["sections"]["company-information"]["sections"][
        "contact-person"
    ]["fields"][social_security_field.identifier] = {
        "value": "010181-900C",
        "extraValue": "",
    }
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "y-tunnus"
    ] = {"value": "1234567-8", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "hallintaosuus"
    ] = {"value": "1/1", "extraValue": ""}

    answer_data = {
        "form": basic_template_form.id,
        "user": admin_user.id,
        "entries": entries,
        "targets": [plot_search_target.pk,],  # noqa: E231
    }

    answer_serializer = AnswerSerializer(data=answer_data)
    # test that a correctly formatted ssn passes the validator
    assert answer_serializer.is_valid()

    answer_data["entries"]["hakijan-tiedot"]["sections"]["company-information"][
        "sections"
    ]["contact-person"]["fields"][social_security_field.identifier] = {
        "value": "010181G900C",
        "extraValue": "",
    }
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(raise_exception=True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "invalid_ssn"

    answer_data["entries"]["hakijan-tiedot"]["sections"]["company-information"][
        "sections"
    ]["contact-person"]["fields"][social_security_field.identifier] = {
        "value": "010181-900D",
        "extraValue": "",
    }
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(raise_exception=True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "invalid_ssn"


@pytest.mark.django_db
def test_company_id_validator(
    django_db_setup, basic_template_form, plot_search_target, admin_user
):
    entries = {}
    for section in basic_template_form.sections.filter(parent__isnull=True):
        entries[section.identifier] = dict()
        generate_entries(section, entries[section.identifier])
    entries["hakijan-tiedot"]["sections"]["company-information"]["sections"][
        "contact-person"
    ]["fields"]["henkilotunnus"] = {"value": "010181-900C", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "y-tunnus"
    ] = {"value": "1234567-8", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "hallintaosuus"
    ] = {"value": "1/1", "extraValue": ""}

    answer_data = {
        "form": basic_template_form.id,
        "user": admin_user.id,
        "entries": entries,
        "targets": [plot_search_target.pk,],  # noqa: E231
    }

    answer_serializer = AnswerSerializer(data=answer_data)
    # test that a correctly formatted ssn passes the validator
    assert answer_serializer.is_valid()

    answer_data["entries"]["hakijan-tiedot"]["sections"]["company-information"][
        "fields"
    ]["y-tunnus"] = {"value": "12345A7-8", "extraValue": ""}
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(raise_exception=True)
    assert val_error.value.args[0]["non_field_errors"][0].code == "invalid_company_id"


@pytest.mark.django_db
def test_control_share(
    django_db_setup, basic_template_form, plot_search_target, admin_user
):
    entries = {}
    for section in basic_template_form.sections.filter(parent__isnull=True):
        entries[section.identifier] = dict()
        generate_entries(section, entries[section.identifier])
    entries["hakijan-tiedot"]["sections"]["company-information"]["sections"][
        "contact-person"
    ]["fields"]["henkilotunnus"] = {"value": "010181-900C", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "y-tunnus"
    ] = {"value": "1234567-8", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"]["company-information"]["fields"][
        "hallintaosuus"
    ] = {"value": "1/3", "extraValue": ""}
    entries["hakijan-tiedot"]["sections"].update(
        {
            "company-information[0]": {
                "fields": {
                    "hallintaosuus": {"value": "2/3", "extraValue": "",},  # noqa: E231
                }
            }
        }
    )

    answer_data = {
        "form": basic_template_form.id,
        "user": admin_user.id,
        "entries": entries,
        "targets": [plot_search_target.pk,],  # noqa: E231
    }

    answer_serializer = AnswerSerializer(data=answer_data)
    # test that a correctly formatted ssn passes the validator
    assert answer_serializer.is_valid()

    answer_data["entries"]["hakijan-tiedot"]["sections"]["company-information[0]"][
        "fields"
    ]["hallintaosuus"] = {"value": "1/3", "extraValue": ""}
    answer_serializer = AnswerSerializer(data=answer_data)

    # test that a incorrectly formatted ssn is caught by the validator
    with pytest.raises(ValidationError) as val_error:
        answer_serializer.is_valid(raise_exception=True)
    assert (
        val_error.value.args[0]["non_field_errors"][0].code
        == "control share is not even"
    )


@pytest.mark.django_db
def test_target_status(
    django_db_setup,
    user,
    area_search_test_data,
    basic_template_form,
    plot_search_target,
    answer_factory,
):
    answer = answer_factory(form=basic_template_form, user=user)
    plot_search_target.answers.add(answer)
    plot_search_target.save()

    assert TargetStatus.objects.all().count() == 1

    target_status_data = {
        "identifier": "91-21-21-21",
        "share_of_rental_indicator": 2,
        "share_of_rental_denominator": 3,
        "reserved": True,
        "added_target_to_applicant": True,
        "counsel_date": timezone.now(),
        "decline_reason": DeclineReason.APPLICATION_EXPIRED,
        "arguments": "Very good arguments",
        "proposed_managements": [],
        "meeting_memos": [
            {
                "meeting_memo": SimpleUploadedFile(
                    name="example.txt", content=b"Lorem lipsum"
                )
            }
        ],
        "reservation_conditions": ["Very good condition",],  # noqa: E23
        "geometry": area_search_test_data.geometry.geojson,
    }

    target_status_serializer = TargetStatusSerializer(data=target_status_data)

    assert target_status_serializer.is_valid()
