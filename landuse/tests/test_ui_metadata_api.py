import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("admin_client")]


@pytest.fixture(autouse=True)
def enable_landuse_api(settings):
    settings.FLAG_LANDUSE_API_ENABLED = True


def test_ui_metadata_returns_choices_and_cache_headers(admin_client):
    url = reverse("v1:landuse-ui-metadata")

    response = admin_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["agreement_statuses"] == [
        {"value": "DRAFT", "label": "Luonnos"},
        {"value": "IN_PROGRESS", "label": "Vireillä"},
        {"value": "NEGOTIATION", "label": "Neuvottelu"},
        {"value": "DECISION", "label": "Päätös"},
        {"value": "SIGNATURE", "label": "Allekirjoitus"},
        {"value": "NO_AGREEMENT", "label": "Ei sopimusta"},
    ]
    assert response["Cache-Control"] == (
        "public, max-age=86400, stale-while-revalidate=604800"
    )
    assert "ETag" in response


def test_ui_metadata_honors_if_none_match(admin_client):
    url = reverse("v1:landuse-ui-metadata")
    initial_response = admin_client.get(url)

    cached_response = admin_client.get(url, HTTP_IF_NONE_MATCH=initial_response["ETag"])

    assert cached_response.status_code == status.HTTP_304_NOT_MODIFIED
    assert cached_response["ETag"] == initial_response["ETag"]
    assert cached_response["Cache-Control"] == initial_response["Cache-Control"]
