import pytest
from django.core.management import call_command

from forms.models import Form


@pytest.mark.django_db
def test_generate_default_plotsearch_forms_command():
    Form.objects.all().delete()
    form_count = len(Form.objects.filter(is_template=True))
    call_command("generate_default_plotsearch_forms")
    new_form_count = len(Form.objects.filter(is_template=True))
    assert form_count < new_form_count
