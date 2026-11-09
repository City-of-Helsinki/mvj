import pytest
from django.urls import reverse
from django_countries import countries
from rest_framework import status

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("admin_client")]


@pytest.fixture(autouse=True)
def enable_landuse_api(settings):
    settings.FLAG_LANDUSE_API_ENABLED = True


def test_ui_metadata_returns_choices(admin_client):
    url = reverse("v1:landuse-ui-metadata")

    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["countries"] == [
        {"value": code, "label": str(label)} for code, label in countries
    ]
    assert response.json()["agreement_statuses"] == [
        {"value": "draft", "label": "Luonnos"},
        {"value": "in_progress", "label": "Vireillä"},
        {"value": "negotiation", "label": "Neuvottelu"},
        {"value": "decision", "label": "Päätös"},
        {"value": "signature", "label": "Allekirjoitus"},
        {"value": "no_agreement", "label": "Ei sopimusta"},
    ]
