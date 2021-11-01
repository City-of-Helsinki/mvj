import pytest

from forms.models import Field, FieldType, Section
from forms.utils import clone_object


@pytest.mark.django_db
def test_form_cloning(basic_template_form):
    section_count = Section.objects.all().count()
    field_count = Field.objects.all().count()
    fieldtype_count = FieldType.objects.all().count()

    new_form = clone_object(basic_template_form)

    new_section_count = Section.objects.all().count()
    new_field_count = Field.objects.all().count()
    new_fieldtype_count = FieldType.objects.all().count()

    assert new_form.id != basic_template_form
    assert new_section_count == section_count * 2
    assert new_field_count == field_count * 2
    assert new_fieldtype_count == fieldtype_count
