import pytest
from django.utils.text import slugify
from faker import Faker

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_section_identifier(form_factory, section_factory):
    title = fake.name()
    form = form_factory(title=fake.name())
    section = section_factory(form=form, title=title)

    expected_slug = slugify(title)
    assert expected_slug == section.identifier


@pytest.mark.django_db
def test_linking_answer_to_form(form_factory, answer_factory, user_factory):
    form = form_factory(title=fake.name())
    user = user_factory(username=fake.name())
    answer = answer_factory(form=form, user=user)
    assert answer.form_id == form.id


@pytest.mark.django_db
def test_linking_entry_to_answer(
    form_factory,
    answer_factory,
    entry_section_factory,
    entry_factory,
    user_factory,
    field_factory,
    field_type_factory,
    section_factory,
):
    form = form_factory(title=fake.name())
    user = user_factory(username=fake.name())
    answer = answer_factory(form=form, user=user)
    field_type = field_type_factory(name=fake.name(), identifier=slugify(fake.name()))
    section = section_factory(form=form, title=fake.name())
    field = field_factory(
        label=fake.name(),
        hint_text=fake.name(),
        identifier=slugify(fake.name()),
        validation=fake.name(),
        action=fake.name(),
        type=field_type,
        section=section,
    )
    entry_section = entry_section_factory(answer=answer)
    entry = entry_factory(entry_section=entry_section, field=field, value=fake.name())
    assert entry.entry_section.answer_id == answer.id
