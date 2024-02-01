from pathlib import Path

import factory
import pytest
from django.core.management import call_command
from faker import Faker

from forms.models import Answer

fake = Faker("fi_FI")


@pytest.fixture
def basic_template_form_with_required_fields(basic_template_form):
    sections = basic_template_form.sections.all()
    for section in sections:
        if section.identifier != "person-information":
            continue
        for field in section.fields.all():
            field.required = True
            field.save()

    return basic_template_form


@pytest.fixture
def basic_form_data():
    return {
        "name": fake.name(),
        "description": fake.sentence(),
        "is_template": False,
        "title": fake.sentence(),
    }


@pytest.fixture
def basic_form(basic_template_form):
    basic_template_form.is_template = False
    basic_template_form.save()
    return basic_template_form


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Loads all the database fixtures in the plotsearch/fixtures and leasing/fixtures folder"""
    fixture_path = Path(__file__).parents[1].parent / "plotsearch/fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    # Remove field_types.json from fixtures, because it is run in migration.
    for path in fixture_filenames:
        if "field_types.json" in path.name:
            fixture_filenames.remove(path)

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)

    fixture_path = Path(__file__).parents[1].parent / "leasing/fixtures"
    fixture_filenames = [path for path in fixture_path.glob("*") if not path.is_dir()]

    with django_db_blocker.unblock():
        call_command("loaddata", *fixture_filenames)


class AnswerFactory(factory.DjangoModelFactory):
    class Meta:
        model = Answer
