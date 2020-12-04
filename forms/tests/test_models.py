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
