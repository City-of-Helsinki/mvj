import pytest
from faker import Faker
from rest_framework.reverse import reverse

from forms.models.form import EntrySection
from plotsearch.enums import InformationState

fake = Faker("fi_FI")


@pytest.mark.django_db
def test_information_check(admin_client, admin_user, basic_answer):
    entry_section = EntrySection.objects.all().first()
    entry_section.metadata = {"identifier": "010170-1234", "type": "person"}
    entry_section.save()
    url = reverse("informationcheck-list")
    data = {
        "name": fake.name(),
        "answer": basic_answer.pk,
        "state": InformationState.CHECKED,
        "preparer": admin_user.pk,
        "comment": fake.name(),
        "identifier": "010170-1234",
        "type": "person",
        "mark_all": True,
    }
    response = admin_client.post(url, data=data, content_type="application/json")
    assert response.status_code == 201

    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.data["results"][0]["answer"] == basic_answer.pk
